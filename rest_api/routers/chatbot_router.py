from fastapi import APIRouter, HTTPException, Depends, Request
import requests
import pandas as pd
import json
import psycopg2
from typing import Dict, Any
from rest_api.clova_api import call_hyperclova
from prompts.prs_cns_prompt import (PROMPT_revenue, PROMPT_engagement, PROMPT_communication,
                                    PROMPT_targeting, PROMPT_popular_videos, PROMPT_thumbnail,
                                    PROMPT_upload_pattern, PROMPT_activity, PROMPT_summary)
        
prompts = {
    'revenue': PROMPT_revenue,
    'engagement': PROMPT_engagement,
    'communication': PROMPT_communication,
    'targeting': PROMPT_targeting,
    'popular_videos': PROMPT_popular_videos,
    'thumbnail': PROMPT_thumbnail,
    'upload_pattern': PROMPT_upload_pattern,
    'activity': PROMPT_activity,
    'summary' : PROMPT_summary
}

chatbot_router = APIRouter()

class CompletionExecutor:
    def __init__(self):
        self._host = "https://clovastudio.stream.ntruss.com"
        self._api_key = "Bearer nv-f5786fde571f424786ed0823986ca992h3P1"

    def execute(self, prompt_type: str, metrics: Dict[str, Any], max_tokens: int = 150):
        prompt = prompts[prompt_type]
        formatted_prompt = [
            prompt[0],
            {"role": "user", "content": prompt[1]["content"].format(**metrics)}
        ]

        request_data = {
            "messages": formatted_prompt,
            "topP": 0.8,
            "maxTokens": max_tokens,
            "temperature": 0.15,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": False,
            "seed": 0,
        }

        headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
        }
        
        response_content = ""
        with requests.post(
            self._host + "/testapp/v1/chat-completions/HCX-003", headers=headers, json=request_data, stream=True
        ) as r:
            for line in r.iter_lines():
                if line:
                    data = line.decode("utf-8")
                    if data.startswith("data:"):
                        json_data = json.loads(data[5:])
                        if "message" in json_data and "content" in json_data["message"]:
                            response_content = json_data["message"]["content"]
        return response_content

def get_formatted_prompt(prompt_type: str, metrics: Dict[str, Any]):
    prompt = prompts[prompt_type]
    formatted_prompt = [
        prompt[0],
        {"role": "user", "content": prompt[1]["content"].format(**metrics)}
    ]
    return formatted_prompt

def get_db_engine(request: Request):
    """
    FastAPI의 상태 객체에서 DB 엔진을 가져옵니다.
    """
    return request.app.state.db_engine

conn = psycopg2.connect(host="10.28.224.177", port="30634", user="postgres", password="0104", database="postgres")
query = f"""
    SELECT "id", "title"
    FROM "Channel";
    """
with conn.cursor() as cur:
    id_df = pd.read_sql(query, conn)
    name_to_id = {name: int(id) for name, id in zip(id_df["title"].values, id_df["id"].values)}


###################
## 채널 수익성 API ##
###################
@chatbot_router.get("/profitability/revenue-analysis/{channel_name}")
async def analyze_revenue(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 채널 수익성 분석"""
    def safe_convert(value, default=0):
        if pd.isna(value) or value is None:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    try:
        channel_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT dc.channel_id as "id", dc."totalSubscriberCount" as "subscriberCount"
            FROM public."DailyChannel" dc
            CROSS JOIN latest_date l
            WHERE dc.channel_id = '{name_to_id[channel_name]}'
            AND dc.date = l.max_date
        """
        channel_df = pd.read_sql(channel_query, db_engine)
        if channel_df.empty:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        channel_id = int(channel_df.iloc[0]['id'])
        subscriber_count = float(channel_df.iloc[0]['subscriberCount'])
        
        total_channels_query = "SELECT COUNT(*) as count FROM \"Channel\""
        total_channels = pd.read_sql(total_channels_query, db_engine).iloc[0]['count']

        revenue_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            channel_metrics AS (
                SELECT 
                    dc.channel_id as id,
                    dc."totalViewCount" as view_count,
                    c."Donation" as donation
                FROM public."DailyChannel" dc
                JOIN public."Channel" c ON c.id = dc.channel_id
                CROSS JOIN latest_date l
                WHERE dc.date = l.max_date
            ),
            channel_ranks AS (
                SELECT 
                    cm.id,
                    RANK() OVER (ORDER BY cm.view_count DESC) as view_rank,
                    RANK() OVER (ORDER BY cm.donation DESC) as donation_rank
                FROM channel_metrics cm
            ),
            avg_metrics AS (
                SELECT 
                    AVG(dc."totalViewCount") as avg_views,
                    AVG(c."Donation") as avg_donation
                FROM public."DailyChannel" dc
                JOIN public."Channel" c ON c.id = dc.channel_id
                CROSS JOIN latest_date l
                WHERE dc.date = l.max_date
                AND CAST(dc."totalSubscriberCount" AS FLOAT) 
                BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
            )
            SELECT 
                cm.view_count,
                cm.donation,
                cr.view_rank,
                cr.donation_rank,
                am.avg_views,
                am.avg_donation
            FROM channel_metrics cm
            JOIN channel_ranks cr ON cm.id = cr.id
            CROSS JOIN avg_metrics am
            WHERE cm.id = '{channel_id}'
        """
        
        revenue_df = pd.read_sql(revenue_query, db_engine)
        
        viewcount = safe_convert(revenue_df.iloc[0]["view_count"])
        avg_viewcount = safe_convert(revenue_df.iloc[0]["avg_views"])
        view_profit_user = int((viewcount * 2 + viewcount * 4.5) / 2)
        view_profit_avg = int((avg_viewcount * 2 + avg_viewcount * 4.5) / 2)

        ad_query = f"""
            WITH video_metrics AS (
                SELECT
                    COUNT(*) as ad_count,
                    SUM(CAST("videoViewCount" AS FLOAT)) as total_views,
                    SUM(CAST("videoLikeCount" AS FLOAT)) as total_likes,
                    SUM(CAST("commentCount" AS FLOAT)) as total_comments
                FROM "Video"
                WHERE "channel_id" = '{channel_id}' 
                AND "hasPaidProductPlacement" = true
                AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            ),
            ad_ranks AS (
                SELECT 
                    v."channel_id",
                    RANK() OVER (ORDER BY COUNT(*) DESC) as ad_count_rank
                FROM "Video" v
                WHERE v."hasPaidProductPlacement" = true
                GROUP BY v."channel_id"
            )
            SELECT 
                vm.*,
                ar.ad_count_rank
            FROM video_metrics vm
            CROSS JOIN ad_ranks ar
            WHERE ar.channel_id = '{channel_id}'
        """
        
        ad_df = pd.read_sql(ad_query, db_engine)

        comparison_query = f"""
            WITH video_stats AS (
                SELECT
                    "hasPaidProductPlacement",
                    COUNT(*) as video_count,
                    COUNT(*) / 3.0 as monthly_rate,
                    AVG(CAST("videoViewCount" AS FLOAT)) as avg_views,
                    AVG(CAST("videoLikeCount" AS FLOAT) / NULLIF(CAST("videoViewCount" AS FLOAT), 0) * 100) as avg_like_ratio,
                    AVG(CAST("commentCount" AS FLOAT) / NULLIF(CAST("videoViewCount" AS FLOAT), 0) * 100) as avg_comment_ratio
                FROM "Video"
                WHERE "channel_id" = '{channel_id}'
                AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                GROUP BY "hasPaidProductPlacement"
            )
            SELECT * FROM video_stats
        """
        
        comparison_df = pd.read_sql(comparison_query, db_engine)

        ad_ratio_query = f"""
            WITH channel_ad_ratios AS (
                SELECT 
                    channel_id,
                    COUNT(*) FILTER (WHERE "hasPaidProductPlacement" = true)::float / 
                    NULLIF(COUNT(*), 0) * 100 as ad_ratio
                FROM "Video"
                GROUP BY channel_id
            )
            SELECT RANK() OVER (ORDER BY ad_ratio DESC) as ad_ratio_rank
            FROM channel_ad_ratios
            WHERE channel_id = '{channel_id}'
        """
        
        ad_ratio_df = pd.read_sql(ad_ratio_query, db_engine)
        
        metrics = {
            "view_profit_user": view_profit_user,
            "view_profit_avg": view_profit_avg,
            "donation_profit_user": safe_convert(revenue_df.iloc[0]['donation']),
            "donation_profit_avg": safe_convert(revenue_df.iloc[0]['avg_donation']),
            "view_rank": safe_convert(revenue_df.iloc[0]['view_rank']),
            "donation_rank": safe_convert(revenue_df.iloc[0]['donation_rank']),
            "total_channels": total_channels,
            "ad_count": safe_convert(ad_df.iloc[0]['ad_count']) if not ad_df.empty else 0,
            "ad_count_rank": safe_convert(ad_df.iloc[0]['ad_count_rank']) if not ad_df.empty else 0,
            "total_views": safe_convert(ad_df.iloc[0]['total_views']) if not ad_df.empty else 0,
            "total_likes": safe_convert(ad_df.iloc[0]['total_likes']) if not ad_df.empty else 0,
            "total_comments": safe_convert(ad_df.iloc[0]['total_comments']) if not ad_df.empty else 0,
            "normal_count": safe_convert(comparison_df[comparison_df['hasPaidProductPlacement']==False]['video_count'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==False].empty else 0,
            "ad_count": safe_convert(comparison_df[comparison_df['hasPaidProductPlacement']==True]['video_count'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==True].empty else 0,
            "normal_update_rate": round(float(comparison_df[comparison_df['hasPaidProductPlacement']==False]['monthly_rate'].iloc[0]), 1) if not comparison_df[comparison_df['hasPaidProductPlacement']==False].empty else 0.0,
            "ad_update_rate": round(float(comparison_df[comparison_df['hasPaidProductPlacement']==True]['monthly_rate'].iloc[0]), 1) if not comparison_df[comparison_df['hasPaidProductPlacement']==True].empty else 0.0,
            "normal_view_avg": safe_convert(comparison_df[comparison_df['hasPaidProductPlacement']==False]['avg_views'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==False].empty else 0,
            "ad_view_avg": safe_convert(comparison_df[comparison_df['hasPaidProductPlacement']==True]['avg_views'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==True].empty else 0,
            "normal_like_ratio": float(comparison_df[comparison_df['hasPaidProductPlacement']==False]['avg_like_ratio'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==False].empty else 0.0,
            "ad_like_ratio": float(comparison_df[comparison_df['hasPaidProductPlacement']==True]['avg_like_ratio'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==True].empty else 0.0,
            "normal_comment_ratio": float(comparison_df[comparison_df['hasPaidProductPlacement']==False]['avg_comment_ratio'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==False].empty else 0.0,
            "ad_comment_ratio": float(comparison_df[comparison_df['hasPaidProductPlacement']==True]['avg_comment_ratio'].iloc[0]) if not comparison_df[comparison_df['hasPaidProductPlacement']==True].empty else 0.0,
            "ad_ratio_rank": safe_convert(ad_ratio_df.iloc[0]['ad_ratio_rank']) if not ad_ratio_df.empty else 0
        }

        total_videos = metrics['normal_count'] + metrics['ad_count']
        metrics['ad_ratio'] = (metrics['ad_count'] / total_videos * 100) if total_videos > 0 else 0
        metrics['view_comparison_ratio'] = metrics['ad_view_avg'] / metrics['normal_view_avg'] if metrics['normal_view_avg'] > 0 else 0
        metrics['like_comparison_ratio'] = metrics['ad_like_ratio'] / metrics['normal_like_ratio'] if metrics['normal_like_ratio'] > 0 else 0
        metrics['comment_comparison_ratio'] = metrics['ad_comment_ratio'] / metrics['normal_comment_ratio'] if metrics['normal_comment_ratio'] > 0 else 0

        competitor_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            competitor_metrics AS (
                SELECT 
                    AVG(CAST("videoViewCount" AS FLOAT)) as avg_views,
                    AVG(CAST("videoLikeCount" AS FLOAT)) as avg_likes,
                    AVG(CAST("commentCount" AS FLOAT)) as avg_comments
                FROM "Video" v
                JOIN public."DailyChannel" dc ON v.channel_id = dc.channel_id
                CROSS JOIN latest_date l
                WHERE v."hasPaidProductPlacement" = true
                AND dc.date = l.max_date
                AND CAST(dc."totalSubscriberCount" AS FLOAT) 
                BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
                AND v.channel_id != '{channel_id}'
                AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            )
            SELECT * FROM competitor_metrics
        """
        competitor_df = pd.read_sql(competitor_query, db_engine)

        metrics['avg_views_per_video'] = metrics['total_views'] / metrics['ad_count'] if metrics['ad_count'] > 0 else 0
        metrics['avg_likes_per_video'] = metrics['total_likes'] / metrics['ad_count'] if metrics['ad_count'] > 0 else 0
        metrics['avg_comments_per_video'] = metrics['total_comments'] / metrics['ad_count'] if metrics['ad_count'] > 0 else 0

        competitor_avg_views = float(competitor_df.iloc[0]['avg_views']) if not competitor_df.empty and not pd.isna(competitor_df.iloc[0]['avg_views']) else 1
        competitor_avg_likes = float(competitor_df.iloc[0]['avg_likes']) if not competitor_df.empty and not pd.isna(competitor_df.iloc[0]['avg_likes']) else 1
        competitor_avg_comments = float(competitor_df.iloc[0]['avg_comments']) if not competitor_df.empty and not pd.isna(competitor_df.iloc[0]['avg_comments']) else 1

        metrics['view_ratio'] = metrics['avg_views_per_video'] / competitor_avg_views if competitor_avg_views > 0 else 0
        metrics['like_ratio'] = metrics['avg_likes_per_video'] / competitor_avg_likes if competitor_avg_likes > 0 else 0
        metrics['comment_ratio'] = metrics['avg_comments_per_video'] / competitor_avg_comments if competitor_avg_comments > 0 else 0
        
        formatted_prompt = get_formatted_prompt('revenue', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15, max_tokens=250)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

###################
## 시청자 관계 API ##
###################
@chatbot_router.get("/audience/engagement-analysis/{channel_name}")
async def analyze_engagement(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 시청자 참여도 분석"""
    def safe_round(value, decimals=2):
        if pd.isna(value) or value is None:
            return 0.0
        return round(float(value), decimals)
    try:
        channel_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT "totalSubscriberCount" as "subscriberCount"
            FROM public."DailyChannel" dc
            CROSS JOIN latest_date l
            WHERE dc.channel_id = '{name_to_id[channel_name]}'
            AND dc.date = l.max_date
        """
        channel_info = pd.read_sql(channel_query, db_engine)
        subscriber_count = channel_info.iloc[0]["subscriberCount"]

        upload_count_query = f"""
            SELECT COUNT(*) as video_count
            FROM public."Video" v
            WHERE v."channel_id" = '{name_to_id[channel_name]}'
            AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        """

        engagement_query = f"""
            SELECT 
                SUM(CAST(v."videoViewCount" AS INTEGER)) as total_views,
                SUM(CAST(v."videoLikeCount" AS INTEGER)) as total_likes,
                SUM(CAST(v."commentCount" AS INTEGER)) as total_comments,
                SUM(CAST(v."videoShareCount" AS INTEGER)) as total_shares
            FROM public."Video" v
            WHERE v."channel_id" = '{name_to_id[channel_name]}'
            AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        """

        competitor_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            competitor_metrics AS (
                SELECT 
                    v.channel_id,
                    SUM(CAST(v."videoViewCount" AS INTEGER)) as total_views,
                    SUM(CAST(v."videoLikeCount" AS INTEGER)) as total_likes,
                    SUM(CAST(v."commentCount" AS INTEGER)) as total_comments,
                    SUM(CAST(v."videoShareCount" AS INTEGER)) as total_shares
                FROM public."Video" v
                JOIN public."DailyChannel" dc ON v.channel_id = dc.channel_id
                CROSS JOIN latest_date l
                WHERE dc.date = l.max_date
                AND CAST(dc."totalSubscriberCount" AS INTEGER) 
                    BETWEEN CAST({subscriber_count} AS INTEGER) - 500000 
                    AND CAST({subscriber_count} AS INTEGER) + 500000
                AND v.channel_id != '{name_to_id[channel_name]}'
                AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                GROUP BY v.channel_id
            )
            SELECT 
                AVG((total_likes::float / NULLIF(total_views, 0)) * 100) as avg_like_ratio,
                AVG((total_comments::float / NULLIF(total_views, 0)) * 100) as avg_comment_ratio,
                AVG((total_shares::float / NULLIF(total_views, 0)) * 100) as avg_share_ratio
            FROM competitor_metrics
        """
        upload_count_df = pd.read_sql(upload_count_query, db_engine)
        df = pd.read_sql(engagement_query, db_engine)
        competitor_df = pd.read_sql(competitor_query, db_engine)

        video_count = int(upload_count_df.iloc[0]["video_count"]) if not upload_count_df.empty else 0
        total_views = float(df.iloc[0]["total_views"]) if df.iloc[0]["total_views"] is not None else 0
        total_likes = float(df.iloc[0]["total_likes"]) if df.iloc[0]["total_likes"] is not None else 0
        total_comments = float(df.iloc[0]["total_comments"]) if df.iloc[0]["total_comments"] is not None else 0
        total_shares = float(df.iloc[0]["total_shares"]) if df.iloc[0]["total_shares"] is not None else 0

        metrics = {
            "video_count": video_count,
            "like_ratio": safe_round((total_likes / total_views * 100) if total_views > 0 else 0),
            "comment_ratio": safe_round((total_comments / total_views * 100) if total_views > 0 else 0),
            "share_ratio": safe_round((total_shares / total_views * 100) if total_views > 0 else 0),
            "avg_like_ratio": safe_round(competitor_df.iloc[0]["avg_like_ratio"] if not competitor_df.empty else 0),
            "avg_comment_ratio": safe_round(competitor_df.iloc[0]["avg_comment_ratio"] if not competitor_df.empty else 0),
            "avg_share_ratio": safe_round(competitor_df.iloc[0]["avg_share_ratio"] if not competitor_df.empty else 0)
        }

        formatted_prompt = get_formatted_prompt('engagement', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/audience/communication-analysis/{channel_name}")
async def analyze_communication(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 크리에이터 소통 분석"""
    try:
        # 채널 구독자 수 확인 (경쟁 채널 범위 설정용)
        channel_info_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT 
                CAST(dc."totalSubscriberCount" AS INTEGER) as "subscriberCount",
                c."DisplayName"
            FROM public."DailyChannel" dc
            JOIN public."Channel" c ON c.id = dc.channel_id
            CROSS JOIN latest_date l
            WHERE dc.channel_id = '{name_to_id[channel_name]}'
            AND dc.date = l.max_date
        """
        channel_info = pd.read_sql(channel_info_query, db_engine)
        subscriber_count = channel_info.iloc[0]["subscriberCount"]
        display_name = channel_info.iloc[0]["DisplayName"]

        # 라이브 방송 관련 데이터
        live_query = f"""
            SELECT 
                CAST("LiveBroadcastingCount" AS INTEGER) as live_count,
                CAST("LiveBroadcastingViewer" AS INTEGER) as live_viewers
            FROM public."Channel"
            WHERE "id" = '{name_to_id[channel_name]}'
        """

        # 경쟁 채널들의 라이브 방송 평균
        competitor_live_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT COALESCE(AVG(CAST(c."LiveBroadcastingCount" AS FLOAT)), 0) as avg_competitor_live
            FROM public."Channel" c
            JOIN public."DailyChannel" dc ON c.id = dc.channel_id
            CROSS JOIN latest_date l
            WHERE dc.date = l.max_date
            AND CAST(dc."totalSubscriberCount" AS INTEGER) 
                BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
            AND c.id != '{name_to_id[channel_name]}'
        """

        # 크리에이터 댓글 수
        reply_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT COUNT(*) as reply_count
            FROM public."Channel" ch
            JOIN public."DailyChannel" dc ON ch.id = dc.channel_id
            CROSS JOIN latest_date l
            JOIN public."Video" v ON v."channel_id" = ch."id"
            JOIN public."Comments" cm ON cm."vId" = v."vId"
                AND strpos(cm."replies", '@' || ch."DisplayName") > 0
            WHERE dc.date = l.max_date
            AND ch."id" = '{name_to_id[channel_name]}'
        """

        # 경쟁 채널들의 평균 댓글 수
        competitor_replies_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            reply_counts AS (
                SELECT 
                    ch."id",
                    COUNT(*) as reply_count
                FROM public."Channel" ch
                JOIN public."DailyChannel" dc ON ch.id = dc.channel_id
                CROSS JOIN latest_date l
                JOIN public."Video" v ON v."channel_id" = ch."id"
                JOIN public."Comments" cm ON cm."vId" = v."vId"
                    AND strpos(cm."replies", '@' || ch."DisplayName") > 0
                WHERE dc.date = l.max_date
                AND CAST(dc."totalSubscriberCount" AS INTEGER)
                    BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
                AND ch."id" != '{name_to_id[channel_name]}'
                GROUP BY ch."id"
            )
            SELECT COALESCE(AVG(reply_count), 0) as avg_competitor_replies
            FROM reply_counts
        """

        # 순위 쿼리 (라이브 방송 기준)
        live_rank_query = f"""
            SELECT COUNT(*) + 1 as live_rank
            FROM public."Channel"
            WHERE CAST("LiveBroadcastingCount" AS INTEGER) > (
                SELECT CAST("LiveBroadcastingCount" AS INTEGER)
                FROM public."Channel"
                WHERE "id" = '{name_to_id[channel_name]}'
            )
        """

        # 댓글 순위 쿼리
        reply_rank_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            reply_counts AS (
                SELECT 
                    ch."id",
                    COUNT(*) as reply_count
                FROM public."Channel" ch
                JOIN public."DailyChannel" dc ON ch.id = dc.channel_id
                CROSS JOIN latest_date l
                JOIN public."Video" v ON v."channel_id" = ch."id"
                JOIN public."Comments" cm ON cm."vId" = v."vId"
                    AND strpos(cm."replies", '@' || ch."DisplayName") > 0
                WHERE dc.date = l.max_date
                GROUP BY ch."id"
            )
            SELECT COUNT(*) + 1 as reply_rank
            FROM reply_counts
            WHERE reply_count > (
                SELECT reply_count
                FROM reply_counts
                WHERE "id" = '{name_to_id[channel_name]}'
            )
        """

        # 유사 규모 채널 수와 순위 쿼리
        similar_size_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT COUNT(*) as similar_size_channels
            FROM public."DailyChannel" dc
            CROSS JOIN latest_date l
            WHERE dc.date = l.max_date
            AND CAST(dc."totalSubscriberCount" AS INTEGER)
                BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
        """
        total_channels_query = "SELECT COUNT(*) as total_channels FROM public.\"Channel\""

        total_channels_df = pd.read_sql(total_channels_query, db_engine)

        # 쿼리 실행
        live_df = pd.read_sql(live_query, db_engine)
        competitor_live_df = pd.read_sql(competitor_live_query, db_engine)
        reply_df = pd.read_sql(reply_query, db_engine)
        competitor_replies_df = pd.read_sql(competitor_replies_query, db_engine)
        live_rank_df = pd.read_sql(live_rank_query, db_engine)
        reply_rank_df = pd.read_sql(reply_rank_query, db_engine)
        similar_size_df = pd.read_sql(similar_size_query, db_engine)
        
        metrics = {
            "live_count": int(live_df.iloc[0]["live_count"]) if not live_df.empty and live_df.iloc[0]["live_count"] is not None else 0,
            "live_rank": int(live_rank_df.iloc[0]["live_rank"]) if not live_rank_df.empty and live_rank_df.iloc[0]["live_rank"] is not None else 0,
            "avg_competitor_live": round(float(competitor_live_df.iloc[0]["avg_competitor_live"]), 1) if not competitor_live_df.empty and competitor_live_df.iloc[0]["avg_competitor_live"] is not None else 0,
            "live_viewers": int(live_df.iloc[0]["live_viewers"]) if not live_df.empty and live_df.iloc[0]["live_viewers"] is not None else 0,
            "reply_count": int(reply_df.iloc[0]["reply_count"]) if not reply_df.empty and reply_df.iloc[0]["reply_count"] is not None else 0,
            "reply_rank": int(reply_rank_df.iloc[0]["reply_rank"]) if not reply_rank_df.empty and reply_rank_df.iloc[0]["reply_rank"] is not None else 0,
            "avg_competitor_replies": int(competitor_replies_df.iloc[0]["avg_competitor_replies"]) if not competitor_replies_df.empty and competitor_replies_df.iloc[0]["avg_competitor_replies"] is not None else 0,
            "similar_size_channels": int(similar_size_df.iloc[0]["similar_size_channels"]) if not similar_size_df.empty and similar_size_df.iloc[0]["similar_size_channels"] is not None else 0,
            "live_similar_rank": int(live_rank_df.iloc[0]["live_rank"]) if not live_rank_df.empty and live_rank_df.iloc[0]["live_rank"] is not None else 0,
            "reply_similar_rank": int(reply_rank_df.iloc[0]["reply_rank"]) if not reply_rank_df.empty and reply_rank_df.iloc[0]["reply_rank"] is not None else 0,
            "total_channels": int(total_channels_df.iloc[0]["total_channels"]) if not total_channels_df.empty and total_channels_df.iloc[0]["total_channels"] is not None else 0  # 추가
        }

        formatted_prompt = get_formatted_prompt('communication', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/audience/targeting-analysis/{channel_name}")
async def analyze_targeting(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 시청자 타겟팅 분석"""
    try:
        # 키워드 추출 (태그와 설명의 해시태그)
        keyword_query = f"""
            SELECT 
                v.tags,
                v."videoDescription"
            FROM public."Video" v
            WHERE v."channel_id" = '{name_to_id[channel_name]}'
            AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        """
        
        # 업로드 시간대
        upload_time_query = f"""
            SELECT 
                SUBSTRING(v."videoPublishedAt", 12, 2) AS upload_hour,
                COUNT(*) as upload_count
            FROM public."Video" v
            WHERE v."channel_id" = '{name_to_id[channel_name]}'
            AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            GROUP BY upload_hour
            ORDER BY upload_count DESC
            LIMIT 3
        """

        # 시청 시간대 (댓글 시간 기준)
        view_time_query = f"""
            SELECT 
                SUBSTRING(c."commentPublishedAt", 12, 2) AS view_hour,
                COUNT(*) AS comment_count
            FROM public."Comments" c
            JOIN public."Video" v ON c."vId" = v."vId"
            WHERE v."channel_id" = '{name_to_id[channel_name]}'
            AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            GROUP BY view_hour
            ORDER BY comment_count DESC
            LIMIT 3
        """

        # 업로드 수와 순위
        upload_stats_query = f"""
            WITH upload_counts AS (
                SELECT 
                    channel_id,
                    COALESCE(COUNT(*), 0) as upload_count
                FROM public."Video"
                WHERE CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                GROUP BY channel_id
            )
            SELECT 
                COALESCE((SELECT upload_count FROM upload_counts WHERE channel_id = '{name_to_id[channel_name]}'), 0) as upload_count,
                COALESCE((
                    SELECT COUNT(*) + 1
                    FROM upload_counts
                    WHERE upload_count > (
                        SELECT upload_count 
                        FROM upload_counts 
                        WHERE channel_id = '{name_to_id[channel_name]}'
                    )
                ), 0) as upload_rank
        """

        # 광고 영상 비율
        ad_ratio_query = f"""
            WITH channel_ratios AS (
                SELECT 
                    channel_id,
                    CAST(SUM(CASE WHEN "hasPaidProductPlacement" = true THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) * 100 as ad_ratio
                FROM public."Video"
                GROUP BY channel_id
            )
            SELECT 
                (SELECT ad_ratio FROM channel_ratios WHERE channel_id = '{name_to_id[channel_name]}') as ad_ratio,
                (SELECT AVG(ad_ratio) FROM channel_ratios) as avg_ad_ratio,
                (
                    SELECT COUNT(*) + 1
                    FROM channel_ratios
                    WHERE ad_ratio > (
                        SELECT ad_ratio 
                        FROM channel_ratios 
                        WHERE channel_id = '{name_to_id[channel_name]}'
                    )
                ) as ad_ratio_rank
        """

        # 전체 채널 수
        total_channels_query = "SELECT COUNT(*) as total_channels FROM public.\"Channel\""

        keyword_df = pd.read_sql(keyword_query, db_engine)
        upload_time_df = pd.read_sql(upload_time_query, db_engine)
        view_time_df = pd.read_sql(view_time_query, db_engine)
        upload_stats_df = pd.read_sql(upload_stats_query, db_engine)
        ad_ratio_df = pd.read_sql(ad_ratio_query, db_engine)
        total_channels_df = pd.read_sql(total_channels_query, db_engine)

        # 키워드 추출 및 처리
        all_keywords = []
        for tags in keyword_df["tags"]:
            if tags:
                all_keywords.extend(
                    [tag.strip("#").strip("{}").lower().replace('"', "").replace("\\", "").replace("\n", "")
                        for tag in tags.split(",")]
                )
        for desc in keyword_df["videoDescription"]:
            if desc:
                all_keywords.extend(
                    [word.strip("#").lower().replace('"', "").replace("\\", "").replace("\n", "")
                        for word in desc.split("#")
                        if word.strip()]
                )
        
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = [k for k, v in keyword_counts.most_common(10) if len(k) < 15]

        metrics = {
            "keywords": ", ".join(top_keywords),
            "upload_times": ", ".join([f"{h}시" for h in upload_time_df["upload_hour"].tolist()]) if not upload_time_df.empty else "",
            "upload_time_details": ", ".join([f"{h}시({c}개)" for h, c in zip(upload_time_df["upload_hour"].tolist(), upload_time_df["upload_count"].tolist())]) if not upload_time_df.empty else "",  # 새로운 메트릭 추가
            "viewing_times": ", ".join([f"{h}시" for h in view_time_df["view_hour"].tolist()]) if not view_time_df.empty else "",
            "upload_count": int(upload_stats_df.iloc[0]["upload_count"]) if not upload_stats_df.empty and upload_stats_df.iloc[0]["upload_count"] is not None else 0,
            "total_channels": int(total_channels_df.iloc[0]["total_channels"]) if not total_channels_df.empty and total_channels_df.iloc[0]["total_channels"] is not None else 0,
            "ad_ratio": float(ad_ratio_df.iloc[0]["ad_ratio"]) if not ad_ratio_df.empty and ad_ratio_df.iloc[0]["ad_ratio"] is not None else 0,
            "avg_ad_ratio": float(ad_ratio_df.iloc[0]["avg_ad_ratio"]) if not ad_ratio_df.empty and ad_ratio_df.iloc[0]["avg_ad_ratio"] is not None else 0,
            "ad_ratio_rank": int(ad_ratio_df.iloc[0]["ad_ratio_rank"]) if not ad_ratio_df.empty and ad_ratio_df.iloc[0]["ad_ratio_rank"] is not None else 0,
            "upload_rank": int(upload_stats_df.iloc[0]["upload_rank"]) if not upload_stats_df.empty and upload_stats_df.iloc[0]["upload_rank"] is not None else 0
        }

        formatted_prompt = get_formatted_prompt('targeting', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


###################
## 채널 성과 API ##
###################
@chatbot_router.get("/performance/popular-videos-analysis/{channel_name}")
async def analyze_popular_videos(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 인기 영상 분석"""
    try:
        # 인기 영상 쿼리
        popular_videos_query = f"""
            WITH video_metrics AS (
                SELECT 
                    "videoTitle" as title,
                    "videoThumbnails" as thumbnail,
                    CAST("videoViewCount" AS FLOAT) as view_count,
                    CAST("videoAPV" AS FLOAT) as retention_rate,
                    CAST(("commentCount"::FLOAT / NULLIF("videoViewCount"::FLOAT, 0) * 100) as FLOAT) as comment_rate,
                    CAST(("videoLikeCount"::FLOAT / NULLIF("videoViewCount"::FLOAT, 0) * 100) as FLOAT) as like_rate,
                    CAST("videoCTR" AS FLOAT) as ctr,
                    CAST("videoViewCount" AS FLOAT) / (
                        SELECT AVG(CAST("videoViewCount" AS FLOAT))
                        FROM public."Video"
                        WHERE "channel_id" = '{name_to_id[channel_name]}'
                        AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                    ) as view_ratio
                FROM public."Video"
                WHERE "channel_id" = '{name_to_id[channel_name]}'
                AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            )
            SELECT *
            FROM video_metrics
            ORDER BY view_count DESC, retention_rate DESC
            LIMIT 3
        """

        # 쿼리 실행
        df = pd.read_sql(popular_videos_query, db_engine)
        
        # metrics 구성
        metrics = {
            # 첫 번째 영상
            "title1": df.iloc[0]["title"] if not df.empty else "",
            #"thumbnail1": df.iloc[0]["thumbnail"] if not df.empty else "",
            "view_count1": float(df.iloc[0]["view_count"]) if not df.empty and df.iloc[0]["view_count"] is not None else 0,
            "retention_rate1": float(df.iloc[0]["retention_rate"]) if not df.empty and df.iloc[0]["retention_rate"] is not None else 0,
            "comment_rate1": float(df.iloc[0]["comment_rate"]) if not df.empty and df.iloc[0]["comment_rate"] is not None else 0,
            "like_rate1": float(df.iloc[0]["like_rate"]) if not df.empty and df.iloc[0]["like_rate"] is not None else 0,
            "ctr1": float(df.iloc[0]["ctr"]) if not df.empty and df.iloc[0]["ctr"] is not None else 0,
            "view_ratio1": float(df.iloc[0]["view_ratio"]) if not df.empty and df.iloc[0]["view_ratio"] is not None else 0,

            # 두 번째 영상
            "title2": df.iloc[1]["title"] if len(df) > 1 else "",
            #"thumbnail2": df.iloc[1]["thumbnail"] if len(df) > 1 else "",
            "view_count2": float(df.iloc[1]["view_count"]) if len(df) > 1 and df.iloc[1]["view_count"] is not None else 0,
            "retention_rate2": float(df.iloc[1]["retention_rate"]) if len(df) > 1 and df.iloc[1]["retention_rate"] is not None else 0,
            "comment_rate2": float(df.iloc[1]["comment_rate"]) if len(df) > 1 and df.iloc[1]["comment_rate"] is not None else 0,
            "like_rate2": float(df.iloc[1]["like_rate"]) if len(df) > 1 and df.iloc[1]["like_rate"] is not None else 0,
            "ctr2": float(df.iloc[1]["ctr"]) if len(df) > 1 and df.iloc[1]["ctr"] is not None else 0,
            "view_ratio2": float(df.iloc[1]["view_ratio"]) if len(df) > 1 and df.iloc[1]["view_ratio"] is not None else 0,

            # 세 번째 영상
            "title3": df.iloc[2]["title"] if len(df) > 2 else "",
            #"thumbnail3": df.iloc[2]["thumbnail"] if len(df) > 2 else "",
            "view_count3": float(df.iloc[2]["view_count"]) if len(df) > 2 and df.iloc[2]["view_count"] is not None else 0,
            "retention_rate3": float(df.iloc[2]["retention_rate"]) if len(df) > 2 and df.iloc[2]["retention_rate"] is not None else 0,
            "comment_rate3": float(df.iloc[2]["comment_rate"]) if len(df) > 2 and df.iloc[2]["comment_rate"] is not None else 0,
            "like_rate3": float(df.iloc[2]["like_rate"]) if len(df) > 2 and df.iloc[2]["like_rate"] is not None else 0,
            "ctr3": float(df.iloc[2]["ctr"]) if len(df) > 2 and df.iloc[2]["ctr"] is not None else 0,
            "view_ratio3": float(df.iloc[2]["view_ratio"]) if len(df) > 2 and df.iloc[2]["view_ratio"] is not None else 0
        }

        executor = CompletionExecutor()
        formatted_prompt = get_formatted_prompt('popular_videos', metrics)
        result = call_hyperclova(formatted_prompt, temperature=0.15)
        return executor.execute('popular_videos', metrics, max_tokens=150)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/performance/thumbnail-analysis/{channel_name}")
async def analyze_thumbnails(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 썸네일 성과 분석"""
    try:
        # 썸네일 성과 쿼리
        thumbnail_query = f"""
            WITH thumbnail_metrics AS (
                SELECT 
                    "videoTitle" as title,
                    "videoThumbnails" as thumbnail,
                    CAST("videoViewCount" AS FLOAT) as view_count,
                    CAST("videoAPV" AS FLOAT) as apv,
                    CAST(("commentCount"::FLOAT / NULLIF("videoViewCount"::FLOAT, 0) * 100) as FLOAT) as comment_rate,
                    CAST(("videoLikeCount"::FLOAT / NULLIF("videoViewCount"::FLOAT, 0) * 100) as FLOAT) as like_rate,
                    CAST("videoCTR" AS FLOAT) as ctr,
                    CAST("videoCTR" AS FLOAT) / (
                        SELECT AVG(CAST("videoCTR" AS FLOAT))
                        FROM public."Video"
                        WHERE "channel_id" = '{name_to_id[channel_name]}'
                        AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                    ) as ctr_ratio
                FROM public."Video"
                WHERE "channel_id" = '{name_to_id[channel_name]}'
                AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            )
            SELECT *
            FROM thumbnail_metrics
            ORDER BY ctr DESC
            LIMIT 3
        """

        df = pd.read_sql(thumbnail_query, db_engine)
        
        metrics = {
            # 첫 번째 썸네일
            "title1": df.iloc[0]["title"] if not df.empty else "",
            #"thumbnail1": df.iloc[0]["thumbnail"] if not df.empty else "",
            "view_count1": float(df.iloc[0]["view_count"]) if not df.empty and df.iloc[0]["view_count"] is not None else 0,
            "retention_rate1": float(df.iloc[0]["apv"]) if not df.empty and df.iloc[0]["apv"] is not None else 0,
            "comment_rate1": float(df.iloc[0]["comment_rate"]) if not df.empty and df.iloc[0]["comment_rate"] is not None else 0,
            "like_rate1": float(df.iloc[0]["like_rate"]) if not df.empty and df.iloc[0]["like_rate"] is not None else 0,
            "ctr1": float(df.iloc[0]["ctr"]) if not df.empty and df.iloc[0]["ctr"] is not None else 0,
            "ctr_ratio1": float(df.iloc[0]["ctr_ratio"]) if not df.empty and df.iloc[0]["ctr_ratio"] is not None else 0,

            # 두 번째 썸네일
            "title2": df.iloc[1]["title"] if len(df) > 1 else "",
            #"thumbnail2": df.iloc[1]["thumbnail"] if len(df) > 1 else "",
            "view_count2": float(df.iloc[1]["view_count"]) if len(df) > 1 and df.iloc[1]["view_count"] is not None else 0,
            "retention_rate2": float(df.iloc[1]["apv"]) if len(df) > 1 and df.iloc[1]["apv"] is not None else 0,
            "comment_rate2": float(df.iloc[1]["comment_rate"]) if len(df) > 1 and df.iloc[1]["comment_rate"] is not None else 0,
            "like_rate2": float(df.iloc[1]["like_rate"]) if len(df) > 1 and df.iloc[1]["like_rate"] is not None else 0,
            "ctr2": float(df.iloc[1]["ctr"]) if len(df) > 1 and df.iloc[1]["ctr"] is not None else 0,
            "ctr_ratio2": float(df.iloc[1]["ctr_ratio"]) if len(df) > 1 and df.iloc[1]["ctr_ratio"] is not None else 0,

            # 세 번째 썸네일
            "title3": df.iloc[2]["title"] if len(df) > 2 else "",
            #"thumbnail3": df.iloc[2]["thumbnail"] if len(df) > 2 else "",
            "view_count3": float(df.iloc[2]["view_count"]) if len(df) > 2 and df.iloc[2]["view_count"] is not None else 0,
            "retention_rate3": float(df.iloc[2]["apv"]) if len(df) > 2 and df.iloc[2]["apv"] is not None else 0,
            "comment_rate3": float(df.iloc[2]["comment_rate"]) if len(df) > 2 and df.iloc[2]["comment_rate"] is not None else 0,
            "like_rate3": float(df.iloc[2]["like_rate"]) if len(df) > 2 and df.iloc[2]["like_rate"] is not None else 0,
            "ctr3": float(df.iloc[2]["ctr"]) if len(df) > 2 and df.iloc[2]["ctr"] is not None else 0,
            "ctr_ratio3": float(df.iloc[2]["ctr_ratio"]) if len(df) > 2 and df.iloc[2]["ctr_ratio"] is not None else 0
        }

        formatted_prompt = get_formatted_prompt('thumbnail', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/performance/upload-pattern-analysis/{channel_name}")
async def analyze_upload_pattern(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 업로드 주기 분석"""
    try:
        # 월별 업로드 추이 쿼리 (기존 channel_feature API의 쿼리 활용)
        monthly_query = f"""
            SELECT 
                TO_CHAR(DATE_TRUNC('month', CAST("videoPublishedAt" AS DATE)), 'YYYY-MM') AS month,
                COUNT(*) AS videocount
            FROM public."Video"
            WHERE CAST("videoPublishedAt" AS DATE) >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '8 months'
            AND "channel_id" = '{name_to_id[channel_name]}'
            GROUP BY month
            ORDER BY month;
        """
        
        monthly_df = pd.read_sql(monthly_query, db_engine)
        
        # 월별 데이터 포맷팅
        monthly_data = ", ".join([f"{row['month']}: {int(row['videocount'])}개" 
                                for _, row in monthly_df.iterrows()])
        
        # 월평균 업로드 수 계산
        monthly_uploads = round(monthly_df['videocount'].mean(), 1)

        # 전체 비디오 수와 순위 쿼리
        video_stats_query = f"""
            WITH video_counts AS (
                SELECT 
                    channel_id,
                    COUNT(*) as video_count
                FROM public."Video"
                GROUP BY channel_id
            ),
            channel_ranks AS (
                SELECT 
                    channel_id,
                    video_count,
                    RANK() OVER (ORDER BY video_count DESC) as upload_rank
                FROM video_counts
            )
            SELECT 
                video_count,
                upload_rank
            FROM channel_ranks
            WHERE channel_id = '{name_to_id[channel_name]}'
        """
        
        video_stats_df = pd.read_sql(video_stats_query, db_engine)
        
        # 전체 채널 수 쿼리
        total_channels_query = "SELECT COUNT(*) as total_channels FROM public.\"Channel\""
        total_channels_df = pd.read_sql(total_channels_query, db_engine)
        
        metrics = {
            "monthly_data": monthly_data,
            "monthly_uploads": monthly_uploads,
            "video_count": int(video_stats_df.iloc[0]['video_count']) if not video_stats_df.empty else 0,
            "upload_rank": int(video_stats_df.iloc[0]['upload_rank']) if not video_stats_df.empty else 0,
            "total_channels": int(total_channels_df.iloc[0]['total_channels']) if not total_channels_df.empty else 0
        }

        formatted_prompt = get_formatted_prompt('upload_pattern', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/performance/activity-analysis/{channel_name}")
async def analyze_activity(channel_name: str, db_engine=Depends(get_db_engine)):
    try:
        channel_info_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT CAST("totalSubscriberCount" AS INTEGER) as "subscriberCount"
            FROM public."DailyChannel" dc
            CROSS JOIN latest_date l
            WHERE dc.channel_id = '{name_to_id[channel_name]}'
            AND dc.date = l.max_date
        """
        channel_info = pd.read_sql(channel_info_query, db_engine)
        subscriber_count = channel_info.iloc[0]["subscriberCount"]

        # 조회수, 구독자 참여율 등 통계
        view_stats_query = f"""
            WITH channel_views AS (
                SELECT 
                    channel_id,
                    CAST(AVG(CAST("videoViewCount" AS FLOAT)) AS FLOAT) as avg_views,
                    CAST(AVG(CAST("subscriberViewedRatio" AS FLOAT)) AS FLOAT) as view_sub_ratio
                FROM public."Video"
                WHERE CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                GROUP BY channel_id
            )
            SELECT 
                CAST(avg_views AS FLOAT) as avg_views,
                CAST(view_sub_ratio AS FLOAT) as view_sub_ratio,
                (
                    SELECT COUNT(*) + 1
                    FROM channel_views v2
                    WHERE CAST(v2.avg_views AS FLOAT) > CAST((
                        SELECT avg_views
                        FROM channel_views 
                        WHERE channel_id = '{name_to_id[channel_name]}'
                    ) AS FLOAT)
                ) as view_rank
            FROM channel_views
            WHERE channel_id = '{name_to_id[channel_name]}'
        """

        # 경쟁 채널 통계
        competitor_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            competitor_stats AS (
                SELECT 
                    v.channel_id,
                    dc."totalSubscriberCount" as "subscriberCount",
                    AVG(CAST(v."videoViewCount" AS FLOAT)) as avg_views,
                    AVG(CAST(v."subscriberViewedRatio" AS FLOAT)) as view_sub_ratio,
                    COUNT(*) as upload_count
                FROM public."Video" v
                JOIN public."DailyChannel" dc ON v.channel_id = dc.channel_id
                CROSS JOIN latest_date l
                WHERE dc.date = l.max_date
                AND CAST(dc."totalSubscriberCount" AS INTEGER)
                    BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
                AND v.channel_id != '{name_to_id[channel_name]}'
                AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                GROUP BY v.channel_id, dc."totalSubscriberCount"
            )
            SELECT 
                AVG(avg_views) as competitor_avg_view,
                AVG(view_sub_ratio) as competitor_view_sub_ratio,
                AVG(upload_count) as competitor_avg_upload_count
            FROM competitor_stats
        """

        # 90일 간 업로드 수 통계
        upload_query = f"""
            SELECT COUNT(*) as upload_count
            FROM public."Video"
            WHERE channel_id = '{name_to_id[channel_name]}'
            AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        """

        # 전체 채널 수 조회
        total_channels_query = "SELECT COUNT(*) as total_channels FROM public.\"Channel\""

        # 데이터프레임 생성
        view_stats_df = pd.read_sql(view_stats_query, db_engine)
        competitor_df = pd.read_sql(competitor_query, db_engine)
        upload_df = pd.read_sql(upload_query, db_engine)
        total_channels_df = pd.read_sql(total_channels_query, db_engine)

        # 메트릭스 계산
        metrics = {
            "user_avg_view": float(view_stats_df.iloc[0]["avg_views"]) if not view_stats_df.empty and view_stats_df.iloc[0]["avg_views"] is not None else 0,
            "view_rank": int(view_stats_df.iloc[0]["view_rank"]) if not view_stats_df.empty and view_stats_df.iloc[0]["view_rank"] is not None else 0,
            "competitor_avg_view": float(competitor_df.iloc[0]["competitor_avg_view"]) if not competitor_df.empty and competitor_df.iloc[0]["competitor_avg_view"] is not None else 0,
            "competitor_view_sub_ratio": float(competitor_df.iloc[0]["competitor_view_sub_ratio"]) if not competitor_df.empty and competitor_df.iloc[0]["competitor_view_sub_ratio"] is not None else 0,
            "view_subscriber_ratio": float(view_stats_df.iloc[0]["view_sub_ratio"]) if not view_stats_df.empty and view_stats_df.iloc[0]["view_sub_ratio"] is not None else 0,
            "view_sub_ratio_multiplier": round(float(view_stats_df.iloc[0]["view_sub_ratio"]) / float(competitor_df.iloc[0]["competitor_view_sub_ratio"]), 1) if not competitor_df.empty and competitor_df.iloc[0]["competitor_view_sub_ratio"] is not None and float(competitor_df.iloc[0]["competitor_view_sub_ratio"]) != 0 else 0,
            "upload_count": int(upload_df.iloc[0]["upload_count"]) if not upload_df.empty and upload_df.iloc[0]["upload_count"] is not None else 0,
            "competitor_avg_upload_count": round(float(competitor_df.iloc[0]["competitor_avg_upload_count"]) if not competitor_df.empty and competitor_df.iloc[0]["competitor_avg_upload_count"] is not None else 0, 1),
            "total_channels": int(total_channels_df.iloc[0]["total_channels"]) if not total_channels_df.empty and total_channels_df.iloc[0]["total_channels"] is not None else 0,
            "view_rank_percent": round((view_stats_df.iloc[0]["view_rank"] / total_channels_df.iloc[0]["total_channels"]) * 100, 1) if not view_stats_df.empty and not total_channels_df.empty else 0,
        }

        formatted_prompt = get_formatted_prompt('activity', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15, max_tokens=150)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

###################
## SWOT 요약 API ##
###################
@chatbot_router.get("/summary/{channel_name}")
async def analyze_channel_summary(channel_name: str, db_engine=Depends(get_db_engine)):
    """CLOVA X를 이용한 채널 종합 분석"""
    try:
        # 채널 기본 정보 조회
        channel_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT dc.channel_id as "id", 
                dc."totalSubscriberCount" as "subscriberCount", 
                dc."totalViewCount" as "viewCount"
            FROM public."DailyChannel" dc
            CROSS JOIN latest_date l
            WHERE dc.channel_id = '{name_to_id[channel_name]}'
            AND dc.date = l.max_date
        """
        channel_df = pd.read_sql(channel_query, db_engine)
        if channel_df.empty:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        channel_id = int(channel_df.iloc[0]['id'])
        subscriber_count = float(channel_df.iloc[0]['subscriberCount'])

        # 1. 채널 성과 지표 조회
        performance_query = f"""
            WITH base_stats AS (
                SELECT 
                    c."id",
                    AVG(CAST(v."videoViewCount" AS FLOAT)) as avg_video_views,
                    COUNT(v."vId") as recent_uploads
                FROM "Channel" c
                LEFT JOIN "Video" v ON c."id" = v."channel_id"
                    AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                GROUP BY c."id"
            )
            SELECT 
                COALESCE(avg_video_views, 0) as avg_video_views,
                COALESCE(recent_uploads, 0) as recent_uploads,
                COALESCE(RANK() OVER (ORDER BY avg_video_views DESC), 1) as view_rank
            FROM base_stats 
            WHERE id = '{channel_id}'
        """

        # 2. 경쟁 채널 성과 지표
        competitor_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            video_metrics AS (
                SELECT 
                    v.channel_id as "id",
                    AVG(CAST(v."videoViewCount" AS FLOAT)) as avg_views,
                    COUNT(v."vId") as upload_count,
                    AVG(CAST(v."videoLikeCount" AS FLOAT) / NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) * 100 as like_ratio,
                    AVG(CAST(v."commentCount" AS FLOAT) / NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) * 100 as comment_ratio,
                    AVG(CAST(v."videoShareCount" AS FLOAT) / NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) * 100 as share_ratio
                FROM public."DailyChannel" dc
                JOIN public."Video" v ON dc.channel_id = v.channel_id
                CROSS JOIN latest_date l
                WHERE dc.date = l.max_date
                AND CAST(dc."totalSubscriberCount" AS FLOAT) 
                    BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
                AND dc.channel_id != '{channel_id}'
                AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
                GROUP BY v.channel_id
            )
            SELECT 
                COALESCE(AVG(avg_views), 0) as competitor_avg_view,
                COALESCE(AVG(upload_count), 0) as competitor_avg_upload_count,
                COALESCE(AVG(like_ratio), 0) as avg_like_ratio,
                COALESCE(AVG(comment_ratio), 0) as avg_comment_ratio,
                COALESCE(AVG(share_ratio), 0) as avg_share_ratio
            FROM video_metrics
            WHERE avg_views IS NOT NULL
        """

        # 3. 시청자 참여도 지표 조회
        engagement_query = f"""
            SELECT 
                COALESCE(AVG(CAST("videoLikeCount" AS FLOAT) / NULLIF(CAST("videoViewCount" AS FLOAT), 0)) * 100, 0) as like_ratio,
                COALESCE(AVG(CAST("commentCount" AS FLOAT) / NULLIF(CAST("videoViewCount" AS FLOAT), 0)) * 100, 0) as comment_ratio,
                COALESCE(AVG(CAST("videoShareCount" AS FLOAT) / NULLIF(CAST("videoViewCount" AS FLOAT), 0)) * 100, 0) as share_ratio
            FROM "Video"
            WHERE "channel_id" = '{channel_id}'
            AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        """

        # 4. 수익성 지표 조회
        revenue_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            ),
            revenue_ranks AS (
                SELECT 
                    dc.channel_id as "id",
                    dc."totalViewCount" as view_count,
                    c."Donation" as donation,
                    RANK() OVER (ORDER BY dc."totalViewCount" DESC) as view_rank,
                    RANK() OVER (ORDER BY c."Donation" DESC) as donation_rank
                FROM public."DailyChannel" dc
                JOIN public."Channel" c ON c.id = dc.channel_id
                CROSS JOIN latest_date l
                WHERE dc.date = l.max_date
            ),
            competitor_avg AS (
                SELECT 
                    AVG(dc."totalViewCount") as avg_views,
                    AVG(c."Donation") as avg_donation
                FROM public."DailyChannel" dc
                JOIN public."Channel" c ON c.id = dc.channel_id
                CROSS JOIN latest_date l
                WHERE dc.date = l.max_date
                AND CAST(dc."totalSubscriberCount" AS FLOAT) 
                    BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
                AND dc.channel_id != '{channel_id}'
            )
            SELECT 
                COALESCE(r.view_count, 0) as view_count,
                COALESCE(r.donation, 0) as donation,
                COALESCE(r.view_rank, 1) as view_rank,
                COALESCE(r.donation_rank, 1) as donation_rank,
                COALESCE(c.avg_views, 0) as avg_views,
                COALESCE(c.avg_donation, 0) as avg_donation
            FROM revenue_ranks r
            CROSS JOIN competitor_avg c
            WHERE r.id = '{channel_id}'
        """

        # 전체 채널 수 조회
        total_channels_query = "SELECT COUNT(*) as total_channels FROM \"Channel\""
        
        # 쿼리 실행
        performance_df = pd.read_sql(performance_query, db_engine)
        competitor_df = pd.read_sql(competitor_query, db_engine)
        engagement_df = pd.read_sql(engagement_query, db_engine)
        revenue_df = pd.read_sql(revenue_query, db_engine)
        total_channels_df = pd.read_sql(total_channels_query, db_engine)
        
        def safe_float(value, default=0.0):
            try:
                if pd.isna(value) or value is None:
                    return default
                return float(value)
            except:
                return default

        def calculate_revenue(viewcount):
            return int((viewcount * 2 + viewcount * 4.5) / 2)  # CPM 기반 수익 추정
        
        metrics = {
            # 1. 채널 성과
            "user_avg_view": int(safe_float(performance_df.iloc[0]["avg_video_views"]) if not performance_df.empty else 0),
            "view_rank": int(safe_float(performance_df.iloc[0]["view_rank"]) if not performance_df.empty else 1),
            "competitor_avg_view": int(safe_float(competitor_df.iloc[0]["competitor_avg_view"]) if not competitor_df.empty else 0),
            "upload_count": int(safe_float(performance_df.iloc[0]["recent_uploads"]) if not performance_df.empty else 0),
            "competitor_avg_upload_count": round(safe_float(competitor_df.iloc[0]["competitor_avg_upload_count"]) if not competitor_df.empty else 0, 1),
            
            # 2. 시청자 참여도
            "like_ratio": safe_float(engagement_df.iloc[0]["like_ratio"] if not engagement_df.empty else 0),
            "comment_ratio": safe_float(engagement_df.iloc[0]["comment_ratio"] if not engagement_df.empty else 0),
            "share_ratio": safe_float(engagement_df.iloc[0]["share_ratio"] if not engagement_df.empty else 0),
            "avg_like_ratio": safe_float(competitor_df.iloc[0]["avg_like_ratio"] if not competitor_df.empty else 0),
            "avg_comment_ratio": safe_float(competitor_df.iloc[0]["avg_comment_ratio"] if not competitor_df.empty else 0),
            "avg_share_ratio": safe_float(competitor_df.iloc[0]["avg_share_ratio"] if not competitor_df.empty else 0),
            
            # 3. 채널 수익성
            "view_profit_user": calculate_revenue(safe_float(revenue_df.iloc[0]["view_count"] if not revenue_df.empty else 0)),
            "view_profit_avg": calculate_revenue(safe_float(revenue_df.iloc[0]["avg_views"] if not revenue_df.empty else 0)),
            "donation_profit_user": int(safe_float(revenue_df.iloc[0]["donation"] if not revenue_df.empty else 0)),
            "donation_profit_avg": int(safe_float(revenue_df.iloc[0]["avg_donation"] if not revenue_df.empty else 0)),
            "view_rank": int(safe_float(revenue_df.iloc[0]["view_rank"] if not revenue_df.empty else 1)),
            "donation_rank": int(safe_float(revenue_df.iloc[0]["donation_rank"] if not revenue_df.empty else 1)),
            
            # 4. 기타
            "total_channels": int(total_channels_df.iloc[0]["total_channels"] if not total_channels_df.empty else 0)
        }

        formatted_prompt = get_formatted_prompt('summary', metrics)
        return call_hyperclova(formatted_prompt, temperature=0.15)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))