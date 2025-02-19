import psycopg2
#from psycopg2.extras import RealDictCursor
import pandas as pd
from sqlalchemy import create_engine

def get_db_connection():
    return create_engine('postgresql://postgres:0104@10.28.224.177:30634/postgres')

def get_all_data(channel_id):
    conn = get_db_connection()
    #전체 데이터
    channel_df = pd.read_sql("SELECT * FROM public.\"Channel\"", conn)
    video_df = pd.read_sql("SELECT * FROM public.\"Video\"", conn)
    comment_df = pd.read_sql("SELECT * FROM public.\"Comments\"", conn)

    video_df[['videoLikeCount', 'videoViewCount', 'commentCount']] = video_df[['videoLikeCount', 'videoViewCount', 'commentCount']].astype(float)
    channel_df[['viewCount', 'subscriberCount']] = channel_df[['viewCount', 'subscriberCount']].astype(float)


    channel_df = channel_df[channel_df['id'] == channel_id]
    video_df = video_df[video_df['channel_id'] == channel_id]
    
    video_df['channel_id'] = channel_id
    comment_df = comment_df.merge(video_df[['vId', 'channel_id']], on='vId', how='left')
    comment_df = comment_df[comment_df['channel_id'] == channel_id]

    video_df['like_ratio'] = video_df['videoLikeCount'] / video_df['videoViewCount']
    video_df['comment_ratio'] = video_df['commentCount'] / video_df['videoViewCount']

    channel_df['avg_views'] = channel_df['viewCount'] / video_df.shape[0]
    channel_df['views_per_sub'] = channel_df['viewCount'] / channel_df['subscriberCount']

    # conn.close()
    
    return channel_df, video_df, comment_df

def get_performance_metrics(channel_id):
    channel_df, video_df, comment_df = get_all_data(channel_id)
    #월별 업로드 계산
    video_df['month'] = pd.to_datetime(video_df['videoPublishedAt']).dt.strftime('%Y-%m')
    monthly_uploads = video_df.groupby('month').size().to_dict()

    latest_months = sorted(list(monthly_uploads.keys()))[-6:]
    upload_trends = {month: monthly_uploads[month] for month in latest_months}
    return {
        #평균 조회수
        'avg_views': video_df['videoViewCount'].astype(float).mean(),
        #노출 클릭률
        #구독자 변화량, 조회수 변화량
        #업로드 주기
        'monthly_uploads': upload_trends

   }

def get_relation_metrics(channel_id):
   channel_df, video_df, comment_df = get_all_data(channel_id)

   # 현재 채널 지표
   curr_metrics = {
       'live': video_df[video_df['liveBroadcastContent'] == 'true'].shape[0],
       'comment_ratio': video_df['comment_ratio'].mean(),
       'like_ratio': video_df['like_ratio'].mean()
   }

   # 전체 채널 데이터
   conn = get_db_connection()
   all_video_df = pd.read_sql("SELECT * FROM public.\"Video\"", conn)

   all_video_df[['videoLikeCount', 'videoViewCount', 'commentCount']] = all_video_df[['videoLikeCount', 'videoViewCount', 'commentCount']].astype(float)
   all_video_df['like_ratio'] = all_video_df['videoLikeCount'] / all_video_df['videoViewCount']
   all_video_df['comment_ratio'] = all_video_df['commentCount'] / all_video_df['videoViewCount']
   
   # 채널별 지표 계산
   channel_metrics = all_video_df.groupby('channel_id').agg({
       'liveBroadcastContent': lambda x: (x == 'true').sum(),
       'comment_ratio': 'mean',
       'like_ratio': 'mean'
   })

   # 각 지표별 순위와 전체 채널 수 계산
   total_channels = len(channel_metrics)
   ranks = {
       'live': (channel_metrics['liveBroadcastContent'] > curr_metrics['live']).sum() + 1,
       'comment': (channel_metrics['comment_ratio'] > curr_metrics['comment_ratio']).sum() + 1,
       'like': (channel_metrics['like_ratio'] > curr_metrics['like_ratio']).sum() + 1
   }

   return {
       'live_count': curr_metrics['live'],
       'live_rank': ranks['live'],
       'live_total': total_channels,
       'comment_ratio': curr_metrics['comment_ratio'],
       'comment_rank': ranks['comment'],
       'comment_total': total_channels,
       'like_ratio': curr_metrics['like_ratio'],
       'like_rank': ranks['like'],
       'like_total': total_channels,
       'sponsored_ratio': video_df[video_df['hasPaidProductPlacement'] == True].shape[0] / video_df.shape[0] * 100 if video_df.shape[0] > 0 else 0
   }

   
    # return {
    #     #라이브 수
    #     'live_count': video_df[video_df['liveBroadcastContent'] == 'true'].shape[0],
    #     #댓글 비율
    #     'comment_ratio': video_df['comment_ratio'].mean(),
    #     #타 채널 대비 댓글 순위
    #     'comment_rank': comment_rank,
    #     'total_channels': total_channels,
    #     #좋아요 비율
    #     'like_ratio': video_df['like_ratio'].mean(),
    #     #타켓 시청자 특성(연령 성별)
    #     #대댓글 수
    #     #영상 업로드 / 시청 시간 / 공유 비율
    #     #광고 영상 비율
    #     'sponsored_ratio': video_df[video_df['hasPaidProductPlacement'] == True].shape[0] / video_df.shape[0] * 100

    # }    

def get_revenue_metrics(channel_id):
    channel_df, video_df, comment_df = get_all_data(channel_id)
    total_videos = video_df.shape[0]
    return {
        #조회수 및 후원 수입
        #일반 컨텐츠 대비 성과 비교교
        #광고 동영상 수
        'sponsored_count': video_df[video_df['hasPaidProductPlacement'] == True].shape[0],
        #전체 동영상 수 
        'total_videos': video_df.shape[0],
    }

def import_from_db(channel_id, prompt_version):
    metrics_functions = {
        1: get_performance_metrics,
        2: get_relation_metrics,
        3: get_revenue_metrics
    }
    return metrics_functions[prompt_version](channel_id)