#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品数据模型
"""

from . import db
from datetime import datetime

class Product(db.Model):
    """产品模型"""
    __tablename__ = 'products'
    
    # 主要字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    brand_name = db.Column(db.String(100), nullable=False, unique=True, comment='品牌名称')
    title = db.Column(db.String(200), comment='标题')
    year = db.Column(db.Integer, index=True, comment='年份')
    publish_month = db.Column(db.String(7), comment='发布月份 (YYYY-MM)')
    material = db.Column(db.String(100), comment='材质')
    theme_series = db.Column(db.String(100), default='其他', index=True, comment='主题系列')
    print_size = db.Column(db.String(50), default='循环印花料', index=True, comment='印花尺寸')
    inspiration_origin = db.Column(db.Text, comment='设计灵感来源')
    
    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __init__(self, **kwargs):
        """初始化"""
        super(Product, self).__init__(**kwargs)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'brand_name': self.brand_name,
            'title': self.title,
            'year': self.year,
            'publish_month': self.publish_month,
            'material': self.material,
            'theme_series': self.theme_series,
            'print_size': self.print_size,
            'inspiration_origin': self.inspiration_origin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """字符串表示"""
        return f'<Product {self.brand_name}>'
    
    @classmethod
    def get_by_brand_name(cls, brand_name):
        """根据品牌名获取产品"""
        return cls.query.filter_by(brand_name=brand_name).first()
    
    @classmethod
    def get_all_brands(cls):
        """获取所有品牌"""
        return cls.query.all()
    
    @classmethod
    def get_by_year(cls, year):
        """根据年份获取产品"""
        return cls.query.filter_by(year=year).all()
    
    @classmethod
    def get_by_theme_series(cls, theme_series):
        """根据主题系列获取产品"""
        return cls.query.filter_by(theme_series=theme_series).all()
    
    @classmethod
    def search_by_name(cls, name):
        """根据名称搜索产品"""
        return cls.query.filter(cls.brand_name.contains(name)).all()
    
    @classmethod
    def get_statistics(cls):
        """获取统计信息"""
        total_count = cls.query.count()
        years = db.session.query(cls.year).distinct().filter(cls.year.isnot(None)).all()
        themes = db.session.query(cls.theme_series).distinct().filter(cls.theme_series.isnot(None)).all()
        materials = db.session.query(cls.material).distinct().filter(cls.material.isnot(None)).all()
        
        return {
            'total_brands': total_count,
            'years': sorted([y[0] for y in years if y[0]], reverse=True),
            'theme_series': sorted([t[0] for t in themes if t[0]]),
            'materials': sorted([m[0] for m in materials if m[0]])
        } 