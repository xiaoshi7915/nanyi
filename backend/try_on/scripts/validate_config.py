#!/usr/bin/env python3
"""
配置验证工具
用于在启动前验证配置文件是否完整和有效
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.config import settings
from app.utils.exceptions import ConfigurationError


def main():
    """主函数：验证配置"""
    print("=" * 60)
    print("配置验证工具")
    print("=" * 60)
    print()
    
    try:
        # 验证配置
        is_valid, errors = settings.validate()
        
        if is_valid:
            print("✅ 配置验证通过！")
            print()
            print("配置摘要:")
            print(f"  应用名称: {settings.app_name}")
            print(f"  应用版本: {settings.app_version}")
            print(f"  服务器: {settings.host}:{settings.port}")
            print(f"  数据库类型: {settings.db_type}")
            print(f"  数据库: {settings.db_host}:{settings.db_port}/{settings.db_name}")
            print(f"  OSS存储桶: {settings.oss_bucket_name}")
            print(f"  日志级别: {settings.log_level}")
            print(f"  调试模式: {settings.debug}")
            return 0
        else:
            print("❌ 配置验证失败！")
            print()
            print("发现以下错误:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            print()
            print("请检查.env文件并修复上述错误。")
            return 1
    
    except ConfigurationError as e:
        print("❌ 配置验证失败！")
        print()
        print(f"错误: {e.message}")
        if e.detail.get("errors"):
            print()
            print("详细错误:")
            for i, error in enumerate(e.detail["errors"], 1):
                print(f"  {i}. {error}")
        return 1
    
    except Exception as e:
        print(f"❌ 配置验证过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
