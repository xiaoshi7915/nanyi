#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
访问日志数据库模型
"""

from datetime import datetime
from . import db

class AccessLog(db.Model):
    """访问日志表"""
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='访问时间')
    client_ip = db.Column(db.String(45), nullable=False, comment='客户端IP', index=True)
    method = db.Column(db.String(10), nullable=False, comment='请求方法')
    path = db.Column(db.String(255), nullable=False, comment='请求路径', index=True)
    query_string = db.Column(db.Text, comment='查询参数')
    status_code = db.Column(db.Integer, nullable=False, comment='响应状态码', index=True)
    response_time_ms = db.Column(db.Float, comment='响应时间(毫秒)')
    user_agent = db.Column(db.Text, comment='用户代理')
    referer = db.Column(db.String(255), comment='来源页面')
    
    # IP归属地信息
    country = db.Column(db.String(50), comment='国家', index=True)
    region = db.Column(db.String(50), comment='地区')
    city = db.Column(db.String(50), comment='城市')
    isp = db.Column(db.String(100), comment='ISP运营商')
    timezone = db.Column(db.String(50), comment='时区')
    
    # 额外字段
    session_id = db.Column(db.String(64), comment='会话ID', index=True)
    error_message = db.Column(db.Text, comment='错误信息')
    
    # 索引
    __table_args__ = (
        db.Index('idx_timestamp_ip', 'timestamp', 'client_ip'),
        db.Index('idx_path_status', 'path', 'status_code'),
        db.Index('idx_country_region', 'country', 'region'),
    )
    
    def __repr__(self):
        return f'<AccessLog {self.id}: {self.client_ip} {self.method} {self.path}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'client_ip': self.client_ip,
            'method': self.method,
            'path': self.path,
            'query_string': self.query_string,
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'user_agent': self.user_agent,
            'referer': self.referer,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'isp': self.isp,
            'timezone': self.timezone,
            'session_id': self.session_id,
            'error_message': self.error_message
        }
    
    @classmethod
    def create_from_request_data(cls, data):
        """从请求数据创建访问日志"""
        ip_info = data.get('ip_info', {})
        
        return cls(
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat())),
            client_ip=data.get('client_ip'),
            method=data.get('method'),
            path=data.get('path'),
            query_string=data.get('query_string'),
            status_code=data.get('status_code'),
            response_time_ms=data.get('response_time_ms'),
            user_agent=data.get('user_agent'),
            referer=data.get('referer'),
            country=ip_info.get('country'),
            region=ip_info.get('region'),
            city=ip_info.get('city'),
            isp=ip_info.get('isp'),
            timezone=ip_info.get('timezone'),
            session_id=data.get('session_id'),
            error_message=data.get('error')
        )
    
    @classmethod
    def get_access_stats(cls, days=7):
        """获取访问统计"""
        from sqlalchemy import func
        
        # 最近几天的访问统计
        recent_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.session.query(
            func.date(cls.timestamp).label('date'),
            func.count(cls.id).label('total_requests'),
            func.count(func.distinct(cls.client_ip)).label('unique_visitors'),
            func.avg(cls.response_time_ms).label('avg_response_time')
        ).filter(
            cls.timestamp >= recent_date
        ).group_by(
            func.date(cls.timestamp)
        ).order_by(
            func.date(cls.timestamp).desc()
        ).all()
        
        return [
            {
                'date': stat.date.isoformat(),
                'total_requests': stat.total_requests,
                'unique_visitors': stat.unique_visitors,
                'avg_response_time': round(stat.avg_response_time, 2) if stat.avg_response_time else 0
            }
            for stat in stats
        ]
    
    @classmethod
    def get_top_ips(cls, limit=10, days=7):
        """获取访问最多的IP"""
        from sqlalchemy import func
        
        recent_date = datetime.utcnow() - timedelta(days=days)
        
        top_ips = db.session.query(
            cls.client_ip,
            cls.country,
            cls.city,
            func.count(cls.id).label('request_count')
        ).filter(
            cls.timestamp >= recent_date
        ).group_by(
            cls.client_ip, cls.country, cls.city
        ).order_by(
            func.count(cls.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'ip': ip.client_ip,
                'country': ip.country,
                'city': ip.city,
                'request_count': ip.request_count
            }
            for ip in top_ips
        ]
    
    @classmethod
    def get_popular_paths(cls, limit=10, days=7):
        """获取热门访问路径"""
        from sqlalchemy import func
        
        recent_date = datetime.utcnow() - timedelta(days=days)
        
        popular_paths = db.session.query(
            cls.path,
            func.count(cls.id).label('request_count'),
            func.avg(cls.response_time_ms).label('avg_response_time')
        ).filter(
            cls.timestamp >= recent_date,
            cls.status_code == 200
        ).group_by(
            cls.path
        ).order_by(
            func.count(cls.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'path': path.path,
                'request_count': path.request_count,
                'avg_response_time': round(path.avg_response_time, 2) if path.avg_response_time else 0
            }
            for path in popular_paths
        ]

from datetime import timedelta 