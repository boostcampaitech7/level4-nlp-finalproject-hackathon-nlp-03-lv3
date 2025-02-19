from fastapi import APIRouter, HTTPException, Depends, Request
import pandas as pd
import psycopg2
from collections import Counter

dashboard_router = APIRouter()


# 소수점 자르기
def convert_type(x):
    if isinstance(x, float):
        return int(x) if x.is_integer() else x
    return x


# 숫자 직관화
def simplify(x):

    if x is None:
        return 0

    if x >= 1e8:
        return f"{convert_type(round(x/1e8, 1))}억"
    elif x >= 1e4:
        return f"{convert_type(round(x/1e4, 1))}만"
    elif x >= 1e3:
        return f"{convert_type(round(x/1e3, 1))}천"
    else:
        return f"{convert_type(x)}"


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
@dashboard_router.get("/profitability/views-and-donations/{channel_name}")
async def get_views_and_donations(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    조회수 수입 및 후원 수입 데이터를 반환(조회수 수입, 슈퍼챗 및 후원 금액)
    Parameters:
        Channel_name: 유튜브 채널명 (나중에 채널 ID로 변경해야할 것 같음)
    Returns:
        [{
        "조회수_유저": 1,115,132,
        "조회수_평균": 1,000,000,
        #"후원_유저": 568,186,
        #"후원_평균": 123,456
        }]
    """

    # 코드 테스트할 때는 try, except 빼는 것을 추천
    try:
        channel_query = f"""
        WITH latest_date AS (
            SELECT MAX(date) as max_date 
            FROM public."DailyChannel"
        )
        SELECT 
            dc."totalViewCount", 
            "Donation",
            (SELECT AVG(CAST(dc2."totalViewCount" as float)) 
             FROM public."DailyChannel" dc2 
             WHERE dc2.date = latest.max_date) as avg_viewcount,
            (SELECT AVG(CAST("Donation" as float)) 
             FROM public."Channel") as avg_donation
        FROM public."DailyChannel" dc
        CROSS JOIN latest_date latest
        JOIN public."Channel" c ON c.id = dc.channel_id
        WHERE dc.channel_id = '{name_to_id[channel_name]}'
        AND dc.date = latest.max_date
        """
        df = pd.read_sql(channel_query, db_engine)

        # 전처리 코드 추가
        viewcount = int(df.iloc[0]["totalViewCount"])
        avg_viewcount = int(df.iloc[0]["avg_viewcount"])
        view_profit_user = int((viewcount * 2 + viewcount * 4.5) / 2)
        view_profit_avg = int((avg_viewcount * 2 + avg_viewcount * 4.5) / 2)
        donation_profit_user = int(df.iloc[0]["Donation"])
        donation_profit_avg = int(df.iloc[0]["avg_donation"])

    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return [
        {
            "조회수_유저": view_profit_user,
            "조회수_평균": view_profit_avg,
            "후원_유저": donation_profit_user,
            "후원_평균": donation_profit_avg,
        }
    ]


@dashboard_router.get("/profitability/ad-video-status/{channel_name}")
async def get_ad_video_status(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    광고 영상 현황 데이터를 반환
    Parameters:
        channel_name: 유튜브 채널명 (나중에 채널 ID로 변경해야할 것 같음)
    Returns:
        [
            {"광고영상": "35개 (8달 전 업데이트)", "누적 재생": "1.2천만 (영상당 평균 ~~)", "누적 좋아요": "33.8만 (영상당 평균 ~~)", "누적 댓글": "7천만 (영상당 평균 ~~~)"}
        ]

    """
    try:  # 누적 조회수 값 dailychannel에서 받아오도록 수정
        ad_query = f"""
                SELECT
                    COUNT(*) as ad_count,
                    MAX(v."videoPublishedAt") as last_update,
                    SUM(CAST(v."videoViewCount" AS INTEGER)) as total_views,
                    SUM(CAST(v."videoLikeCount" AS INTEGER)) as total_likes,
                    SUM(CAST(v."commentCount" AS INTEGER)) as total_comments
                FROM public."Video" v
                WHERE v."channel_id" = '{name_to_id[channel_name]}'
                AND v."hasPaidProductPlacement" = true
            """

        df = pd.read_sql(ad_query, db_engine)

        ad_count = df.iloc[0]["ad_count"]
        total_views = df.iloc[0]["total_views"]
        total_likes = df.iloc[0]["total_likes"]
        total_comments = df.iloc[0]["total_comments"]

        avg_views = total_views / ad_count if ad_count > 0 else 0
        avg_likes = total_likes / ad_count if ad_count > 0 else 0
        avg_comments = total_comments / ad_count if ad_count > 0 else 0

    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return [
        {
            "광고 영상": f"{simplify(ad_count)}개",
            "누적 조회수": f"{simplify(total_views)}회 (영상 당 평균 {simplify(avg_views)}회)",
            "누적 좋아요": f"{simplify(total_likes)}개 (영상 당 평균 {simplify(avg_likes)}개)",
            "누적 댓글": f"{simplify(total_comments)}개 (영상 당 평균 {simplify(avg_comments)}개)",
        }
    ]


@dashboard_router.get("/profitability/ad-vs-normal/{channel_name}")
async def compare_ad_vs_normal(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    광고 영상과 일반 영상의 성과 비교 데이터를 반환
    Parameters:
        channel_name: 유튜브 채널명 (나중에 채널 ID로 변경해야할 것 같음)
    Returns:
        [{
        "영상 수": {"일반 영상":"368개", "광고 영상":"35개", "비교":"-"},
         "업데이트 주기": {"일반 영상":"월 4개", "광고 영상":"월 2개", "비교":"-"},
         "평균 조회수": {"일반 영상":"100,000회", "광고 영상":"20,000회", "비교":"-80,000"},
         "평균 좋아요 비율": {"일반 영상":"0.2%", "광고 영상":"0.001%", "비교":"-0.199%"},
         "평균 댓글 비율": {"일반 영상":"0.01%", "광고 영상":"0.005%", "비교":"-0.005%"}
         }]
    """
    # 최근 90일
    query = f"""
    WITH ad_stats AS (
        SELECT
            SUM(CAST(v."videoViewCount" AS FLOAT)) AS viewcount,
            SUM(CAST(v."videoLikeCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS likecount,
            SUM(CAST(v."commentCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS commentcount,
            COUNT(*) AS videocount
        FROM public."Video" v
        LEFT JOIN public."Channel" c
        ON v."channel_id" = c."id"
        WHERE v."channel_id" = '{name_to_id[channel_name]}' 
              AND v."hasPaidProductPlacement" = true
              AND CAST(v."videoPublishedAt" AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
    ),
    non_ad_stats AS (
        SELECT
            SUM(CAST(v."videoViewCount" AS FLOAT)) AS viewcount,
            SUM(CAST(v."videoLikeCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS likecount,
            SUM(CAST(v."commentCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS commentcount,
            COUNT(*) AS videocount
        FROM public."Video" v
        LEFT JOIN public."Channel" c
        ON v."channel_id" = c."id"
        WHERE v."channel_id" = '{name_to_id[channel_name]}' 
              AND v."hasPaidProductPlacement" = false
              AND CAST(v."videoPublishedAt" AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
    )
    SELECT 
        non_ad_stats.viewcount, 
        non_ad_stats.likecount, 
        non_ad_stats.commentcount, 
        non_ad_stats.videocount,
        ad_stats.viewcount AS ad_viewcount, 
        ad_stats.likecount AS ad_likecount, 
        ad_stats.commentcount AS ad_commentcount, 
        ad_stats.videocount AS ad_videocount
    FROM non_ad_stats, ad_stats
    """

    # 전체
    # query = f"""
    #     WITH compare AS (
    #             SELECT
    #                     SUM(CAST(v."videoViewCount" AS FLOAT))  AS viewcount,
    #                     SUM(CAST(v."videoLikeCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS likecount,
    #                     SUM(CAST(v."commentCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS commentcount,
    #                     COUNT(*) AS videocount
    #             FROM public."Video" v
    #             LEFT JOIN public."Channel" c
    #             ON v."channel_id" = c."id"
    #             WHERE v."channel_id" = '{name_to_id[channel_name]}' AND v."hasPaidProductPlacement" = false
    #             UNION ALL
    #             SELECT
    #                     SUM(CAST(v."videoViewCount" AS FLOAT)) AS viewcount,
    #                     SUM(CAST(v."videoLikeCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS likecount,
    #                     SUM(CAST(v."commentCount" AS FLOAT)/NULLIF(CAST(v."videoViewCount" AS FLOAT), 0)) AS commentcount,
    #                     COUNT(*) AS videocount
    #             FROM public."Video" v
    #             LEFT JOIN public."Channel" c
    #             ON v."channel_id" = c."id"
    #             WHERE v."channel_id" = '{name_to_id[channel_name]}' AND v."hasPaidProductPlacement" = true
    #     )
    #     SELECT *
    #     FROM compare
    #     """
    try:
        df = pd.read_sql(query, db_engine)
        if df.empty:
            raise HTTPException(status_code=404, detail="Channel not found.")

        # 영상 수
        video_count = int(df.iloc[0]["videocount"]) if df.iloc[0]["videocount"] != None else 0
        ads_video_count = int(df.iloc[0]["ad_videocount"]) if df.iloc[0]["ad_videocount"] != None else 0
        # 업데이트 주기
        period = convert_type(round(video_count / 3, 1))
        ads_period = convert_type(round(ads_video_count / 3, 1))
        # 평균 조회수
        view_count = int(df.iloc[0]["viewcount"]) // video_count if video_count != 0 else 0  # 전체 조회수
        ads_view_count = (
            int(df.iloc[0]["ad_viewcount"]) // ads_video_count if ads_video_count != 0 else 0
        )  # 광고 영상 조회수
        # 평균 좋아요 비율
        like_ratio = df.iloc[0]["likecount"] / video_count * 100 if video_count != 0 else 0  # 전체 좋아요 합산
        ads_like_ratio = (
            df.iloc[0]["ad_likecount"] / ads_video_count * 100 if ads_video_count != 0 else 0
        )  # 광고 영상 좋아요 합산
        # 평균 댓글 비율
        comment_ratio = df.iloc[0]["commentcount"] / video_count * 100 if video_count != 0 else 0  # 전체 댓글 합산
        ads_comment_ratio = (
            df.iloc[0]["ad_commentcount"] / ads_video_count * 100 if ads_video_count != 0 else 0
        )  # 광고 영상 좋아요 합산

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return [
        {
            "영상 수": {"일반 영상": f"{video_count:,}개", "광고 영상": f"{ads_video_count:,}개", "비교": "-"},
            "업데이트 주기": {"일반 영상": f"월 {period}개", "광고 영상": f"월 {ads_period}개", "비교": "-"},
            "평균 조회수": {
                "일반 영상": f"{view_count:,}",
                "광고 영상": f"{ads_view_count:,}",
                "비교": f"{ads_view_count-view_count:,}",
            },
            "평균 좋아요 비율": {
                "일반 영상": f"{round(like_ratio,2)}%",
                "광고 영상": f"{round(ads_like_ratio,2)}%",
                "비교": f"{round(ads_like_ratio-like_ratio, 2)}%",
            },
            "평균 댓글 비율": {
                "일반 영상": f"{round(comment_ratio,2)}%",
                "광고 영상": f"{round(ads_comment_ratio,2)}%",
                "비교": f"{round(ads_comment_ratio-comment_ratio,2)}%",
            },
        }
    ]

# 광고 영상 성적
@dashboard_router.get("/profitability/ad-performance/{channel_name}")
async def get_ad_performance(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    성과가 좋은 광고 영상 정보 반환
    Parameters:
        channel_name: 유튜브 채널명
    Returns:
        {
            "가장 성적이 좋은 광고 영상": {
                "제목": "너희는 우리가 직접 상대한다",
                "썸네일": "https://i.ytimg.com/vi/IXITajnvLEc/default.jpg",
                "업로드 날짜": "2024-11-14",
                "조회수": "92.2만",
                "평균 조회율": "48.5%",
                "댓글 참여율": "0.15%",
                "좋아요 참여율": "2.15%",
                "노출 클릭률": "9.0%"
            },
            "가장 성적이 안좋은 광고 영상": {
                "제목": "배우 데뷔를 결심하다",
                "썸네일": "https://i.ytimg.com/vi/7eMS1oMpUSc/default.jpg",
                "업로드 날짜": "2025-01-06",
                "조회수": "28.6만",
                "평균 조회율": "39.8%",
                "댓글 참여율": "0.44%",
                "좋아요 참여율": "1.42%",
                "노출 클릭률": "7.2%"
            }
        }
    """
    # 최근 90일 필터 where에 붙이기 AND CAST("videoPublishedAt" AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
    performance_query = f"""
            WITH metrics AS (
                SELECT 
                    "videoTitle",
                    "videoThumbnails",
                    CAST("videoPublishedAt" AS DATE) as date,
                    CAST("videoViewCount" AS FLOAT) as view_count,
                    "videoAPV" as apv,
                    ROUND((CAST("commentCount" AS FLOAT) / CAST("videoViewCount" AS FLOAT) * 100)::numeric, 2) as comment_rate,
                    ROUND((CAST("videoLikeCount" AS FLOAT) / CAST("videoViewCount" AS FLOAT) * 100)::numeric, 2) as like_rate,
                    ROUND(CAST("videoCTR" AS FLOAT)::numeric, 2) as ctr
                FROM public."Video"
                WHERE "channel_id" = '{name_to_id[channel_name]}'  AND "hasPaidProductPlacement" = true 
            )
            (SELECT 
                "videoTitle" as "제목",
                "videoThumbnails" as "썸네일",
                date as "업로드 날짜",
                view_count as "조회수",
                apv as "평균 조회율",
                comment_rate as "댓글 참여율",
                like_rate as "좋아요 참여율",
                ctr as "노출 클릭률"
            FROM metrics
            ORDER BY "조회수" DESC 
            LIMIT 1)
            UNION ALL
            (SELECT 
                "videoTitle" as "제목",
                "videoThumbnails" as "썸네일",
                date as "업로드 날짜",
                view_count as "조회수",
                apv as "평균 조회율",
                comment_rate as "댓글 참여율",
                like_rate as "좋아요 참여율",
                ctr as "노출 클릭률"
            FROM metrics
            ORDER BY "조회수" ASC 
            LIMIT 1)
        """

    try:  # 조회수 dailyChannel로 수정
        df = pd.read_sql(performance_query, db_engine)
        df["조회수"] = df["조회수"].apply(lambda x: simplify(x))
        df["평균 조회율"] = df["평균 조회율"].apply(lambda x: f"{convert_type(x)}%")
        df["댓글 참여율"] = df["댓글 참여율"].apply(lambda x: f"{convert_type(x)}%")
        df["좋아요 참여율"] = df["좋아요 참여율"].apply(lambda x: f"{convert_type(x)}%")
        df["노출 클릭률"] = df["노출 클릭률"].apply(lambda x: f"{convert_type(x)}%")
        df = df[
            ["제목", "썸네일", "업로드 날짜", "조회수", "평균 조회율", "댓글 참여율", "좋아요 참여율", "노출 클릭률"]
        ]

        result = {
            "가장 성적이 좋은 광고 영상": df.iloc[0].to_dict(),
            "가장 성적이 안좋은 광고 영상": df.iloc[1].to_dict(),
        }

        return result

    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


###################
## 시청자 관계 API ##
###################
@dashboard_router.get("/audience/engagement/{channel_name}")
async def get_audience_engagement(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    시청자의 채널 참여도 데이터를 반환 -> 90일 기준
    Parameters:
        channel_name: 유튜브 채널명
    Returns:
        [{
        "좋아요 비율": "1.90%",
        "댓글 비율": "0.15%",
        "공유 비율": "4.76%"
        }]
    """

    try:
        engagement_query = """
            WITH video_stats AS (
                SELECT 
                    CAST(v."videoViewCount" AS INTEGER) as views,
                    CAST(v."videoLikeCount" AS INTEGER) as likes,
                    CAST(v."commentCount" AS INTEGER) as comments,
                    CAST(v."videoShareCount" AS INTEGER) as shares
                FROM public."Video" v
                WHERE v."channel_id" = %(channel_id)s
                AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            )
            SELECT 
                SUM(vs.views) as total_views,
                SUM(vs.likes) as total_likes,
                SUM(vs.comments) as total_comments,
                SUM(vs.shares) as total_shares,
                MAX(CASE WHEN vs.views > 0 THEN (vs.likes::float / vs.views * 100) END) as max_like_ratio,
                MIN(NULLIF(CASE WHEN vs.views > 0 THEN (vs.likes::float / vs.views * 100) END, 0)) as min_like_ratio,
                MAX(CASE WHEN vs.views > 0 THEN (vs.comments::float / vs.views * 100) END) as max_comment_ratio,
                MIN(NULLIF(CASE WHEN vs.views > 0 THEN (vs.comments::float / vs.views * 100) END, 0)) as min_comment_ratio,
                MAX(CASE WHEN vs.views > 0 THEN (vs.shares::float / vs.views * 100) END) as max_share_ratio,
                MIN(NULLIF(CASE WHEN vs.views > 0 THEN (vs.shares::float / vs.views * 100) END, 0)) as min_share_ratio
            FROM video_stats vs
            """
        df = pd.read_sql(engagement_query, db_engine, params={"channel_id": name_to_id[channel_name]})

        total_views = float(df.iloc[0]["total_views"]) if df.iloc[0]["total_views"] is not None else 0
        total_likes = float(df.iloc[0]["total_likes"]) if df.iloc[0]["total_likes"] is not None else 0
        total_comments = float(df.iloc[0]["total_comments"]) if df.iloc[0]["total_comments"] is not None else 0
        total_shares = float(df.iloc[0]["total_shares"]) if df.iloc[0]["total_shares"] is not None else 0

        like_ratio = (total_likes / total_views * 100) if total_views > 0 else 0
        comment_ratio = (total_comments / total_views * 100) if total_views > 0 else 0
        share_ratio = (total_shares / total_views * 100) if total_views > 0 else 0

        return [{
            "좋아요 비율": f"{like_ratio:.2f}%",
            "댓글 비율": f"{comment_ratio:.2f}%", 
            "공유 비율": f"{share_ratio:.2f}%",
            "최대 좋아요 비율": f"{df.iloc[0]['max_like_ratio'] if df.iloc[0]['max_like_ratio'] is not None else 0:.2f}%",
            "최소 좋아요 비율": f"{df.iloc[0]['min_like_ratio'] if df.iloc[0]['min_like_ratio'] is not None else 0:.2f}%",
            "최대 댓글 비율": f"{df.iloc[0]['max_comment_ratio'] if df.iloc[0]['max_comment_ratio'] is not None else 0:.2f}%",
            "최소 댓글 비율": f"{df.iloc[0]['min_comment_ratio'] if df.iloc[0]['min_comment_ratio'] is not None else 0:.2f}%",
            "최대 공유 비율": f"{df.iloc[0]['max_share_ratio'] if df.iloc[0]['max_share_ratio'] is not None else 0:.2f}%",
            "최소 공유 비율": f"{df.iloc[0]['min_share_ratio'] if df.iloc[0]['min_share_ratio'] is not None else 0:.2f}%"
            }]
    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@dashboard_router.get("/audience/creator-communication/{channel_name}")
async def get_creator_communication(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    크리에이터가 시청자와 소통하는 하는 정도를 나타내는 데이터를 반환
    Parameters:
        channel_name: 유튜브 채널명
    Returns:
        [{
            "라이브 수": int(live_data['LiveBroadcastingCount']),
            "경쟁 채널 라이브 수": int(competitor_live['avg_competitor_live']),
            "라이브 평균 시청자 수": int(live_data['LiveBroadcastingViewer']),
            "대댓글 수": int(replies_data['reply_count']),
            "경쟁 채널 평균 대댓글 수": int(competitor_replies['avg_competitor_replies'])
        }]
    """
    try:
        # 채널의 구독자 수 범위 파악용
        channel_info_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT dc."totalSubscriberCount" as "subscriberCount", c."DisplayName"
            FROM public."DailyChannel" dc
            JOIN public."Channel" c ON c.id = dc.channel_id
            CROSS JOIN latest_date l
            WHERE dc.channel_id = '{name_to_id[channel_name]}'
            AND dc.date = l.max_date
        """
        channel_info = pd.read_sql(channel_info_query, db_engine)
        subscriber_count = channel_info.iloc[0]["subscriberCount"]
        display_name = channel_info.iloc[0]["DisplayName"]  # 현재 채널 아이디 (대댓글 확인용)

        # # PostgreSQL에서 특수문자 처리
        # sescaped_display_name = display_name.replace("'", "''").replace('@', '\\@')

        # 현재 채널의 라이브 수
        live_query = f"""
            SELECT "LiveBroadcastingCount",
                "LiveBroadcastingViewer"
            FROM public."Channel"
            WHERE "id" = '{name_to_id[channel_name]}'
        """

        # 경쟁 채널들의 라이브 수
        competitor_live_query = f"""
            WITH latest_date AS (
                SELECT MAX(date) as max_date 
                FROM public."DailyChannel"
            )
            SELECT 
                COALESCE(AVG(c."LiveBroadcastingCount"), 0) as avg_competitor_live,
                (SELECT MAX(c2."LiveBroadcastingViewer") FROM public."Channel" c2) as max_live_viewer
            FROM public."DailyChannel" dc
            JOIN public."Channel" c ON c.id = dc.channel_id
            CROSS JOIN latest_date l
            WHERE dc.date = l.max_date
            AND CAST(dc."totalSubscriberCount" AS FLOAT) 
            BETWEEN CAST({subscriber_count} AS FLOAT) - 500000 AND CAST({subscriber_count} AS FLOAT) + 500000
            AND dc.channel_id != '{name_to_id[channel_name]}'
        """

        # 대댓글 수 계산
        replies_query = f"""
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

        # # 경쟁 채널들의 평균 대댓글 수
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
                AND CAST(dc."totalSubscriberCount" AS FLOAT) 
                BETWEEN CAST({subscriber_count} AS FLOAT) - 500000 AND CAST({subscriber_count} AS FLOAT) + 500000
                AND ch."id" != '{name_to_id[channel_name]}'
                GROUP BY ch."id"
            )
            SELECT COALESCE(AVG(reply_count), 0) as avg_competitor_replies
            FROM reply_counts
        """

        # 최종 메트릭
        live_data = pd.read_sql(live_query, db_engine).to_dict("records")[0]
        competitor_live = pd.read_sql(competitor_live_query, db_engine).to_dict("records")[0]
        replies_data = pd.read_sql(replies_query, db_engine).to_dict("records")[0]
        competitor_replies = pd.read_sql(competitor_replies_query, db_engine).to_dict("records")[0]

        return [
            {
                "라이브 수": int(live_data["LiveBroadcastingCount"]),
                "경쟁 채널 라이브 수": int(competitor_live["avg_competitor_live"]),
                "라이브 평균 시청자 수": int(live_data["LiveBroadcastingViewer"]),
                "라이브 최대 시청자 수": int(competitor_live["max_live_viewer"]),
                "대댓글 수": int(replies_data["reply_count"]),
                "경쟁 채널 평균 대댓글 수": int(competitor_replies["avg_competitor_replies"]),
            }
        ]

    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@dashboard_router.get("/audience/targeting-strategy/{channel_name}")
async def get_targeting_strategy(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    시청자 타겟팅 전략 데이터를 반환
    Parameters:
        channel_name: 유튜브 채널명
    Returns:
        [{
            "타겟 시청자 특성": "남성", "10~20대", <- 수정
            "키워드": "178만"명, <- Video-tag, description 해시태그 각 키워드 개수 센 후 랭킹, 상위 n개 뽑기, 90일 기준
            "영상 업로드 시간": 12, 1, <- 다시 수정, 90일 기준
            "영상 시청 시간": 12, 1, <- 다시 수정, 90일 기준
            "일반/광고 영상 비율" : 0.3 <- 광고영상이 전체의 30%
        }]
    """
    try:
        video_query = f"""
            SELECT 
                v.tags,
                v."videoDescription"
            FROM public."Video" v
            WHERE v."channel_id" = '{name_to_id[channel_name]}'
            AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        """
        video_df = pd.read_sql(video_query, db_engine)

        all_keywords = []
        for tags in video_df["tags"]:
            if tags:
                all_keywords.extend(
                    [
                        tag.strip("#").strip("{}").lower().replace('"', "").replace("\\", "").replace("\n", "")
                        for tag in tags.split(",")
                    ]
                )
        for description in video_df["videoDescription"]:
            if description:
                all_keywords.extend(
                    [
                        word.strip("#").lower().replace('"', "").replace("\\", "").replace("\n", "")
                        for word in description.split("#")
                        if word.strip()
                    ]
                )

        # 키워드 빈도
        keyword_counts = Counter(all_keywords)
        top_keywords = dict(keyword_counts.most_common())

        # 영상 업로드 시간 분석
        upload_time_query = f"""
            SELECT 
                SUBSTRING(v."videoPublishedAt", 12, 2) AS upload_hour
            FROM public."Video" v
            WHERE v."channel_id" = '{name_to_id[channel_name]}'
            AND CAST(v."videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
            GROUP BY upload_hour
            ORDER BY COUNT(*) DESC
            LIMIT 3
        """
        upload_time_df = pd.read_sql(upload_time_query, db_engine)
        upload_time_list = [
            [int(row["upload_hour"]), int(row["upload_hour"]) + 1] for _, row in upload_time_df.iterrows()
        ]

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
        view_time_df = pd.read_sql(view_time_query, db_engine)
        view_time_list = [[int(row["view_hour"]), int(row["view_hour"]) + 1] for _, row in view_time_df.iterrows()]

        # 일반/광고 영상 비율
        ad_video_query = f"""
            SELECT 
                SUM(CASE WHEN "hasPaidProductPlacement" = true THEN 1 ELSE 0 END) AS ad_count,
                COUNT(*) AS total_count
            FROM public."Video"
            WHERE "channel_id" = '{name_to_id[channel_name]}'
        """
        ad_video_df = pd.read_sql(ad_video_query, db_engine)
        ad_ratio = round(ad_video_df.iloc[0]["ad_count"] / ad_video_df.iloc[0]["total_count"] * 100, 1)

        return [
            {
                "타겟 시청자 특성": "임시값, 임시값",
                "키워드": ", ".join([k for k, v in list(top_keywords.items())[5:11] if len(k) < 15]),
                "영상 업로드 시간": upload_time_list,
                "영상 시청 시간": view_time_list,
                "일반/광고 영상 비율": f"{ad_ratio}%",
            }
        ]

    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


###################
## 채널 성과 API ##
###################


# 채널 배너
@dashboard_router.get("/performance/channel-banner/{channel_name}")
async def get_channel_banner(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    채널 기본 정보 데이터 반환
    Parameters:
        channel_name: 유튜브 채널명
    Returns:
        [{
            "채널 이름": "피식대학",
            "썸네일": "https://yt3.ggpht.com/FQ61Pjh2In6lt-nd0o6EtWyCRPIlopBzcm-Pz88CzRXE1gZQ-o1OnV8wL-9IzC4aRr52M6q4z8I=s88-c-k-c0x00ffffff-no-rj",
            "구독자": "178만"명, #수정, dailyChannel 최근 값으로
            "동영상": "1.2천"개
        }]
    """
    try:
        channel_query = f"""
        WITH latest_date AS (
            SELECT MAX(date) as max_date 
            FROM public."DailyChannel"
        )
        SELECT 
            c."title",
            c."thumbnails" AS "thumbnail",
            CAST(dc."totalSubscriberCount" AS INTEGER) AS "subscriberCount", 
            CAST(c."videoCount" AS INTEGER) AS "videoCount"
        FROM public."Channel" c
        JOIN public."DailyChannel" dc ON c.id = dc.channel_id
        CROSS JOIN latest_date l
        WHERE c."id" = '{name_to_id[channel_name]}'
        AND dc.date = l.max_date
        """

        channel_info = pd.read_sql(channel_query, db_engine)

        return [
            {
                "채널 이름": channel_info.iloc[0]["title"],
                "썸네일": channel_info.iloc[0]["thumbnail"],
                "구독자": simplify(channel_info.iloc[0]["subscriberCount"]) + "명",
                "동영상": simplify(channel_info.iloc[0]["videoCount"]) + "개",
            }
        ]

    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# 많이 사랑 받는 영상 / 많이 사랑 받는 썸네일
@dashboard_router.get("/performance/channel-performance/{channel_name}")
async def get_channel_performance(channel_name: str, db_engine=Depends(get_db_engine)):
    """
        성과가 좋은 영상 정보 반환
        Parameters:
            channel_name: 유튜브 채널명
        Returns:
            {
    "많은 사랑을 받은 영상": [
        {
        "제목": "모텔 주차장을 지나 2평짜리 고시원에 사는 그녀",
        "썸네일": "https://i.ytimg.com/vi/6cvjmXjB-N0/default.jpg",
        "조회수": "453만",
        "평균 조회율": "65.7%",
        "댓글 참여율": "0.05%",
        "좋아요 참여율": "0.72%",
        "노출 클릭률": "6.8%"
        } * 3개
    ],
    "많은 사랑을 받은 썸네일": [
        {
        "제목": "대학 축제 온 30대 처음 봐?",
        "썸네일": "https://i.ytimg.com/vi/OkT1luM9krg/default.jpg",
        "조회수": "21.2만",
        "평균 조회율": "65.7%",
        "댓글 참여율": "0.12%",
        "좋아요 참여율": "1.47%",
        "노출 클릭률": "9.9%"
        } * 3개
    ]
    }
    """
    video_performance_query = f"""
        WITH video_metrics AS (
            SELECT 
                "videoTitle",
                "videoThumbnails",
                CAST("videoViewCount" AS FLOAT) as view_count,
                CAST("videoAPV" AS FLOAT) as apv,
                ROUND((CAST("commentCount" AS FLOAT) / CAST("videoViewCount" AS FLOAT) * 100)::numeric, 2) as comment_rate,
                ROUND((CAST("videoLikeCount" AS FLOAT) / CAST("videoViewCount" AS FLOAT) * 100)::numeric, 2) as like_rate,
                ROUND(CAST("videoCTR" AS FLOAT)::numeric, 2) as ctr
            FROM public."Video"
            WHERE "channel_id" = '{name_to_id[channel_name]}'
            AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        )
        SELECT 
            "videoTitle" as "제목",
            "videoThumbnails" as "썸네일",
            view_count as "조회수",
            apv as "평균 조회율",
            comment_rate as "댓글 참여율",
            like_rate as "좋아요 참여율",
            ctr as "노출 클릭률"
        FROM video_metrics
        ORDER BY view_count DESC, apv DESC
        LIMIT 3
    """

    thumbnail_performance_query = f"""
        WITH thumbnail_metrics AS (
            SELECT 
                "videoTitle",
                "videoThumbnails",
                CAST("videoViewCount" AS FLOAT) as view_count,
                CAST("videoAPV" AS FLOAT) as apv,
                ROUND((CAST("commentCount" AS FLOAT) / CAST("videoViewCount" AS FLOAT) * 100)::numeric, 2) as comment_rate,
                ROUND((CAST("videoLikeCount" AS FLOAT) / CAST("videoViewCount" AS FLOAT) * 100)::numeric, 2) as like_rate,
                ROUND(CAST("videoCTR" AS FLOAT)::numeric, 2) as ctr
            FROM public."Video"
            WHERE "channel_id" = '{name_to_id[channel_name]}'
            AND CAST("videoPublishedAt" AS TIMESTAMP) >= NOW() - INTERVAL '90 days'
        )
        SELECT 
            "videoTitle" as "제목",
            "videoThumbnails" as "썸네일",
            view_count as "조회수",
            apv as "평균 조회율",
            comment_rate as "댓글 참여율",
            like_rate as "좋아요 참여율",
            ctr as "노출 클릭률"
        FROM thumbnail_metrics
        ORDER BY ctr DESC
        LIMIT 3
    """
    try:  # 조회수 dailyChannel로 수정
        top_videos_df = pd.read_sql(video_performance_query, db_engine)
        top_thumbnails_df = pd.read_sql(thumbnail_performance_query, db_engine)

        for df in [top_videos_df, top_thumbnails_df]:
            df["조회수"] = df["조회수"].apply(lambda x: simplify(x))
            df["평균 조회율"] = df["평균 조회율"].apply(lambda x: f"{x}%")
            df["댓글 참여율"] = df["댓글 참여율"].apply(lambda x: f"{x}%")
            df["좋아요 참여율"] = df["좋아요 참여율"].apply(lambda x: f"{x}%")
            df["노출 클릭률"] = df["노출 클릭률"].apply(lambda x: f"{x}%")
            df = df[["제목", "썸네일", "조회수", "평균 조회율", "댓글 참여율", "좋아요 참여율", "노출 클릭률"]]

        result = {
            "많은 사랑을 받은 영상": top_videos_df.to_dict(orient="records"),
            "많은 사랑을 받은 썸네일": top_thumbnails_df.to_dict(orient="records"),
        }

        return result

    except KeyError:
        raise HTTPException(status_code=404, detail="Channel not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# 최근 90일 채널 평균 조회수
@dashboard_router.get("/performance/channel-viewcount/{channel_name}")
async def get_channel_viewcount(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    method 설명
    Parameters:
        channel_name: 유튜브 채널명
    Returns:

    """
    # 채널의 구독자 수 범위 파악용
    channel_info_query = f"""
        WITH latest_date AS (
            SELECT MAX(date) as max_date 
            FROM public."DailyChannel"
        )
        SELECT dc."totalSubscriberCount" as "subscriberCount", c."DisplayName"
        FROM public."DailyChannel" dc
        JOIN public."Channel" c ON c.id = dc.channel_id
        CROSS JOIN latest_date l
        WHERE dc.channel_id = '{name_to_id[channel_name]}'
        AND dc.date = l.max_date
    """
    channel_info = pd.read_sql(channel_info_query, db_engine)
    subscriber_count = channel_info.iloc[0]["subscriberCount"]

    # 현재 채널의 평균 조회수
    user_query = f"""
        SELECT
            COALESCE(AVG(CAST("videoViewCount" AS BIGINT)), 0) AS avg_views
        FROM public."Video"
        WHERE "channel_id" = '{name_to_id[channel_name]}' 
        AND CAST("videoPublishedAt" AS DATE) >= CURRENT_DATE - INTERVAL '90 days';
    """

    # 경쟁 채널들의 조회수
    competitor_query = f"""
        WITH latest_date AS (
            SELECT MAX(date) as max_date 
            FROM public."DailyChannel"
        )
        SELECT 
            COALESCE(AVG(CAST(v."videoViewCount" AS BIGINT)), 0) AS avg_views
        FROM public."Video" v
        JOIN public."DailyChannel" dc ON v.channel_id = dc.channel_id
        CROSS JOIN latest_date l
        WHERE dc.date = l.max_date
        AND CAST(dc."totalSubscriberCount" AS BIGINT) 
            BETWEEN CAST({subscriber_count} AS BIGINT) - 500000 AND CAST({subscriber_count} AS BIGINT) + 500000
        AND v.channel_id != '{name_to_id[channel_name]}'
        AND CAST(v."videoPublishedAt" AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
    """
    
    try:
        user_df = pd.read_sql(user_query, db_engine)
        competitor_df = pd.read_sql(competitor_query, db_engine)
        
        user_avg_view = int(user_df.iloc[0]["avg_views"])
        competitor_avg_view = int(competitor_df.iloc[0]["avg_views"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
        
    return [
        {
            "내 채널 평균 조회수": user_avg_view,
            "경쟁 채널 평균 조회수": competitor_avg_view,
        }
    ]

# 채널 성장 추세
@dashboard_router.get("/performance/channel-growth/{channel_name}")
async def get_channel_growth(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    method 설명
    Parameters:
        channel_name: 유튜브 채널명
    Returns:
        [{
        'x':["2024-11-10", "2024-11-11", "2024-11-12", "2024-11-13", "2024-11-14", ...],
        "구독자 그래프":[2840000.0, 2840000.0, 2840000.0, 2840000.0, 2840000.0, ...],
        "조회수 그래프":{'daily':[597868.0, 430060.0, 518304.0, 810582.0, ...], 'total':[2098252623.0, 2098682683.0, 2099200987.0, ...]}
        }]
    """
    query = f"""
        SELECT * FROM public."DailyChannel"
        WHERE "channel_id" = '{name_to_id[channel_name]}'
        """
    try:
        df = pd.read_sql(query, db_engine)
        if df.empty:
            raise HTTPException(status_code=404, detail="Channel not found.")
        dates = df["date"].to_list()
        total_subscriber = df["totalSubscriberCount"].to_list()
        daily_view = df["dailyViewCount"].to_list()
        total_view = df["totalViewCount"].to_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    return [
        {"x": dates, "구독자 그래프": total_subscriber, "조회수 그래프": {"daily": daily_view, "total": total_view}}
    ]


# 채널 특징
@dashboard_router.get("/performance/channel-feature/{channel_name}")
async def get_channel_feature(channel_name: str, db_engine=Depends(get_db_engine)):
    """
    method 설명
    Parameters:
        channel_name: 유튜브 채널명
    Returns:
        업로드 주기 리스트로
        활성도는 값으로
    """
    # 영상 업로드 주기
    query = f"""
        SELECT 
                TO_CHAR(DATE_TRUNC('month', CAST("videoPublishedAt" AS DATE)), 'YYYY-MM') AS month,
                COUNT(*) AS videocount
        FROM public."Video"
        WHERE CAST("videoPublishedAt" AS DATE) >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
        AND "channel_id" = '{name_to_id[channel_name]}'
        GROUP BY month
        ORDER BY month;
        """
    # 채널 활성도
    sub_query = f"""
        SELECT AVG("subscriberViewedRatio") as avg_participation
        FROM "Video"
        WHERE "channel_id" = '{name_to_id[channel_name]}' AND CAST("videoPublishedAt" AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
        """
    try:
        df = pd.read_sql(query, db_engine)
        sub_df = pd.read_sql(sub_query, db_engine)
        if df.empty:
            raise HTTPException(status_code=404, detail="Channel not found.")
        dates = df["month"].to_list()
        values = df["videocount"].to_list()
        
        # participation이 None인 경우 0으로 처리
        participation = sub_df.iloc[0]["avg_participation"]
        if participation is not None:
            participation = round(participation, 1)
        else:
            participation = 0.0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    return [{"x": dates, "영상 수": values, "참여도": f"{convert_type(participation)}%"}]

#임시
@dashboard_router.get("/profitability/revenue-analysis/{channel_name}")
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
            SELECT "id", "subscriberCount"
            FROM "Channel"
            WHERE "id" = '{name_to_id[channel_name]}'
        """
        channel_df = pd.read_sql(channel_query, db_engine)
        if channel_df.empty:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        channel_id = int(channel_df.iloc[0]['id'])
        subscriber_count = float(channel_df.iloc[0]['subscriberCount'])
        
        # total_channels_query = "SELECT COUNT(*) as count FROM \"Channel\""
        # total_channels = pd.read_sql(total_channels_query, db_engine).iloc[0]['count']

        revenue_query = f"""
            WITH channel_metrics AS (
                SELECT 
                    c."id",
                    CAST(c."viewCount" AS FLOAT) as view_count,
                    CAST(c."Donation" AS FLOAT) as donation
                FROM "Channel" c
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
                    AVG(CAST(c."viewCount" AS FLOAT)) as avg_views,
                    AVG(CAST(c."Donation" AS FLOAT)) as avg_donation,
                    COUNT(*) as total_channels
                FROM "Channel" c
            )
            SELECT 
                cm.view_count,
                cm.donation,
                cr.view_rank,
                cr.donation_rank,
                am.avg_views,
                am.avg_donation,
                am.total_channels
            FROM channel_metrics cm
            JOIN channel_ranks cr ON cm.id = cr.id
            CROSS JOIN avg_metrics am
            WHERE cm.id = '{channel_id}'
        """
        
        revenue_df = pd.read_sql(revenue_query, db_engine)

        viewcount = safe_convert(revenue_df.iloc[0]["view_count"])
        avg_viewcount = safe_convert(revenue_df.iloc[0]["avg_views"])
        total_channels = safe_convert(revenue_df.iloc[0]["total_channels"])

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
            WITH competitor_metrics AS (
                SELECT 
                    AVG(CAST("videoViewCount" AS FLOAT)) as avg_views,
                    AVG(CAST("videoLikeCount" AS FLOAT)) as avg_likes,
                    AVG(CAST("commentCount" AS FLOAT)) as avg_comments
                FROM "Video" v
                JOIN "Channel" c ON v.channel_id = c.id
                WHERE v."hasPaidProductPlacement" = true
                AND CAST(c."subscriberCount" AS FLOAT) 
                BETWEEN {subscriber_count} - 500000 AND {subscriber_count} + 500000
                AND v.channel_id != '{channel_id}'
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

        # executor = CompletionExecutor()
        # return executor.execute('revenue', metrics)
        return {
            "수익 현황": {
                "조회수 수입_유저": f"{metrics['view_profit_user']:,}원",
                "조회수 수입_평균": f"{metrics['view_profit_avg']:,}원",
                "후원 수입_유저": f"{metrics['donation_profit_user']:,}원",
                "후원 수입_평균": f"{metrics['donation_profit_avg']:,}원",
                "조회수 순위": f"{metrics['view_rank']}위 / {metrics['total_channels']}개",
                "후원 순위": f"{metrics['donation_rank']}위 / {metrics['total_channels']}개"
            },
            "광고 영상 현황": {
                "광고 영상 수": f"{metrics['ad_count']}개",
                "광고 영상 순위": f"{metrics['ad_count_rank']}위",
                "누적 조회수": f"{metrics['total_views']:,}회",
                "누적 좋아요": f"{metrics['total_likes']:,}개",
                "누적 댓글": f"{metrics['total_comments']:,}개",
                "영상당 평균 조회수": f"{metrics['avg_views_per_video']:,}회",
                "영상당 평균 좋아요": f"{metrics['avg_likes_per_video']:,}개",
                "영상당 평균 댓글": f"{metrics['avg_comments_per_video']:,}개"
            },
            "광고 vs 일반 영상 비교": {
                "일반 영상 수": f"{metrics['normal_count']}개",
                "광고 영상 비율": f"{metrics['ad_ratio']:.1f}%",
                "조회수 비교": f"일반 영상 {metrics['normal_view_avg']:,}회 vs 광고 영상 {metrics['ad_view_avg']:,}회",
                "좋아요율 비교": f"일반 영상 {metrics['normal_like_ratio']:.2f}% vs 광고 영상 {metrics['ad_like_ratio']:.2f}%",
                "댓글율 비교": f"일반 영상 {metrics['normal_comment_ratio']:.2f}% vs 광고 영상 {metrics['ad_comment_ratio']:.2f}%"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
