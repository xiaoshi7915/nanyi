#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI试衣服务层
封装AI试衣服务API调用，处理与外部AI试衣服务的交互
"""

import os
import requests
from typing import Dict, Optional

from backend.services.base_service import BaseService
from backend.exceptions import ServiceError, NotFoundError


class TryOnService(BaseService):
    """AI试衣服务类 - 封装AI试衣服务API调用"""
    
    def __init__(self):
        """初始化试衣服务"""
        super().__init__(service_name='TryOnService')
        
        # AI试衣服务地址（从环境变量读取，如果没有则使用默认值）
        self.ai_service_base_url = os.environ.get(
            'AI_TRY_ON_SERVICE_URL',
            'http://121.36.205.70:15001'
        )
        
        # 请求超时时间（秒）
        # 状态查询可能需要更长时间，设置为60秒
        self.timeout = int(os.environ.get('AI_TRY_ON_TIMEOUT', '60'))
        
        # 固定参数配置
        # 注意：根据测试脚本，shot_type在真人图模式下会被强制为全身照
        # 但API仍然需要传递shot_type参数（可以是half_body，但实际会生成全身照）
        self.fixed_params = {
            'model_type': 'real',  # 使用真人照片
            'shot_type': 'half_body',  # 注意：真人图模式会强制生成全身照，但API需要这个参数
            'aspect_ratio': '9:16',  # 竖屏，适合手机
            'style': 'portrait_photography'  # 人像摄影风格
        }
        
        self.log_info(f"AI试衣服务初始化: {self.ai_service_base_url}")
    
    def generate_try_on(
        self,
        fabric_image_path: str,
        user_image_file: bytes,
        user_image_filename: str
    ) -> Dict:
        """
        启动AI试衣任务
        
        Args:
            fabric_image_path: 布料图的本地文件路径
            user_image_file: 用户上传的照片文件内容（bytes）
            user_image_filename: 用户上传的照片文件名
        
        Returns:
            dict: 包含task_id和状态信息的字典
        
        Raises:
            NotFoundError: 布料图文件不存在
            ServiceError: AI试衣服务调用失败
        """
        # 检查布料图文件是否存在
        if not os.path.exists(fabric_image_path):
            self.log_error(f"布料图文件不存在: {fabric_image_path}")
            raise NotFoundError(
                message='布料图文件不存在',
                resource_type='fabric_image',
                resource_id=fabric_image_path
            )
        
        # 构建API端点
        api_url = f"{self.ai_service_base_url}/api/v1/try-on/generate"
        
        try:
            # 准备multipart/form-data请求
            # 第一张图片：布料图（从本地文件系统读取）
            with open(fabric_image_path, 'rb') as fabric_file:
                fabric_image_data = fabric_file.read()
            
            # 获取布料图文件名
            fabric_filename = os.path.basename(fabric_image_path)
            
            # 准备文件数据
            # 根据测试脚本，应该使用：
            # - fabric_images: 布料图（单张）
            # - real_person_image: 用户上传的真人照片
            files = [
                ('fabric_images', (fabric_filename, fabric_image_data, 'image/jpeg')),
                ('real_person_image', (user_image_filename, user_image_file, 'image/jpeg'))
            ]
            
            # 准备表单数据（固定参数）
            data = {
                'model_type': self.fixed_params['model_type'],
                'shot_type': self.fixed_params['shot_type'],
                'aspect_ratio': self.fixed_params['aspect_ratio'],
                'style': self.fixed_params['style'],
                'model_provider': 'seedream'  # 添加model_provider参数（测试脚本中有）
            }
            
            self.log_info(f"调用AI试衣服务: {api_url}", 
                         fabric_image=fabric_filename,
                         user_image=user_image_filename)
            
            # 发送POST请求
            response = requests.post(
                api_url,
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应JSON
            result = response.json()
            
            self.log_info(f"AI试衣任务创建成功: task_id={result.get('task_id')}")
            
            return {
                'success': True,
                'task_id': result.get('task_id'),
                'status': result.get('status', 'processing'),
                'estimated_time': result.get('estimated_time', 10)
            }
            
        except requests.exceptions.Timeout:
            self.log_error(f"AI试衣服务请求超时: {api_url}")
            raise ServiceError(
                message='AI试衣服务请求超时，请稍后重试',
                service_name=self.service_name,
                details={'api_url': api_url, 'timeout': self.timeout}
            )
        except requests.exceptions.ConnectionError as e:
            self.log_error(f"AI试衣服务连接失败: {api_url}", error=e)
            raise ServiceError(
                message='无法连接到AI试衣服务，请检查服务是否正常运行',
                service_name=self.service_name,
                details={'api_url': api_url, 'error': str(e)}
            )
        except requests.exceptions.HTTPError as e:
            self.log_error(f"AI试衣服务HTTP错误: {response.status_code}", error=e)
            error_detail = response.text if hasattr(response, 'text') else str(e)
            raise ServiceError(
                message=f'AI试衣服务返回错误: {response.status_code}',
                service_name=self.service_name,
                details={'api_url': api_url, 'status_code': response.status_code, 'error': error_detail}
            )
        except Exception as e:
            self.log_error(f"AI试衣服务调用失败: {api_url}", error=e)
            raise ServiceError(
                message=f'AI试衣服务调用失败: {str(e)}',
                service_name=self.service_name,
                details={'api_url': api_url, 'error': str(e)}
            )
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        查询AI试衣任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: 包含任务状态和结果信息的字典
        
        Raises:
            ServiceError: AI试衣服务调用失败
        """
        # 构建API端点
        api_url = f"{self.ai_service_base_url}/api/v1/try-on/status/{task_id}"
        
        try:
            self.log_debug(f"查询AI试衣任务状态: task_id={task_id}")
            
            # 发送GET请求
            response = requests.get(
                api_url,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应JSON
            result = response.json()
            
            self.log_debug(f"任务状态查询成功: task_id={task_id}, status={result.get('status')}")
            
            return {
                'success': True,
                'status': result.get('status', 'processing'),  # processing, completed, failed
                'result_image_url': result.get('result_image_url'),
                'progress': result.get('progress', 0),
                'error': result.get('error') or result.get('error_message')  # 兼容不同的错误字段名
            }
            
        except requests.exceptions.Timeout:
            self.log_error(f"AI试衣服务请求超时: {api_url}")
            raise ServiceError(
                message='AI试衣服务请求超时，请稍后重试',
                service_name=self.service_name,
                details={'api_url': api_url, 'timeout': self.timeout}
            )
        except requests.exceptions.ConnectionError as e:
            self.log_error(f"AI试衣服务连接失败: {api_url}", error=e)
            raise ServiceError(
                message='无法连接到AI试衣服务，请检查服务是否正常运行',
                service_name=self.service_name,
                details={'api_url': api_url, 'error': str(e)}
            )
        except requests.exceptions.HTTPError as e:
            # 尝试获取响应内容
            error_detail = '未知错误'
            status_code = 500
            if hasattr(e, 'response') and e.response is not None:
                try:
                    status_code = e.response.status_code
                    error_detail = e.response.text[:500] if e.response.text else str(e)
                except:
                    error_detail = str(e)
            else:
                error_detail = str(e)
            
            self.log_error(f"AI试衣服务HTTP错误: {api_url}, status={status_code}", error=e)
            raise ServiceError(
                message=f'AI试衣服务返回错误: {status_code}',
                service_name=self.service_name,
                details={'api_url': api_url, 'status_code': status_code, 'error': error_detail}
            )
        except requests.exceptions.RequestException as e:
            # 处理所有requests相关的异常（包括连接错误、超时等）
            self.log_error(f"AI试衣服务请求异常: {api_url}", error=e)
            raise ServiceError(
                message='无法连接到AI试衣服务，请稍后重试',
                service_name=self.service_name,
                details={'api_url': api_url, 'error': str(e)}
            )
        except Exception as e:
            self.log_error(f"AI试衣服务调用失败: {api_url}", error=e, exc_info=True)
            raise ServiceError(
                message=f'查询任务状态失败: {str(e)}',
                service_name=self.service_name,
                details={'api_url': api_url, 'error': str(e)}
            )
