#!/usr/bin/env python3
"""
测试脚本：通过 HTTP API 创建用户账户

使用管理员账户登录后，通过 /auth/register 端点创建新用户。

使用方法:
    python tests/test_create_user.py
"""

import httpx
import json
from typing import Optional


BASE_URL = "http://127.0.0.1:7864"


def login_admin(username: str = "admin", password: str = "change_this_password") -> Optional[str]:
    """
    管理员登录并获取访问令牌
    
    :param username: 管理员用户名
    :param password: 管理员密码
    :return: 访问令牌，登录失败返回 None
    """
    print(f"📝 正在登录管理员账户: {username}")
    
    try:
        response = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("✅ 管理员登录成功")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None


def create_user(
    token: str,
    username: str,
    password: str,
    role: str = "viewer",
    aliases: Optional[list] = None
) -> bool:
    """
    创建新用户账户
    
    :param token: 管理员访问令牌
    :param username: 新用户名
    :param password: 新用户密码
    :param role: 用户角色 (admin/editor/viewer)
    :param aliases: 用户别名列表
    :return: 创建是否成功
    """
    print(f"\n📝 正在创建用户: {username} (角色: {role})")
    
    try:
        response = httpx.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "password": password,
                "role": role,
                "aliases": aliases or []
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 用户创建成功")
            print(f"   用户ID: {data.get('id')}")
            print(f"   用户名: {data.get('username')}")
            print(f"   角色: {data.get('role')}")
            print(f"   创建时间: {data.get('created_at')}")
            return True
        else:
            print(f"❌ 创建用户失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 创建用户请求失败: {e}")
        return False


def list_users(token: str):
    """
    列出所有用户
    
    :param token: 管理员访问令牌
    """
    print("\n📋 正在获取用户列表...")
    
    try:
        response = httpx.get(
            f"{BASE_URL}/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        
        if response.status_code == 200:
            users = response.json()
            print(f"✅ 共有 {len(users)} 个用户:")
            for user in users:
                print(f"   - {user['username']} ({user['role']}) [{'启用' if user['is_active'] else '禁用'}]")
        else:
            print(f"❌ 获取用户列表失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 获取用户列表请求失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("ComicForge 用户创建测试脚本")
    print("=" * 60)
    
    # 1. 管理员登录
    admin_username = input("\n请输入管理员用户名 [admin]: ").strip() or "admin"
    admin_password = input("请输入管理员密码 [change_this_password]: ").strip() or "change_this_password"
    
    token = login_admin(admin_username, admin_password)
    if not token:
        print("\n💥 无法继续，管理员登录失败")
        return
    
    # 2. 创建用户
    print("\n" + "=" * 60)
    print("创建新用户")
    print("=" * 60)
    
    new_username = input("\n请输入新用户名: ").strip()
    if not new_username:
        print("❌ 用户名不能为空")
        return
    
    new_password = input("请输入新用户密码: ").strip()
    if not new_password:
        print("❌ 密码不能为空")
        return
    
    print("\n选择用户角色:")
    print("  1. viewer  - 查看者（只读权限）")
    print("  2. editor  - 编辑者（读写权限）")
    print("  3. admin   - 管理员（完全权限）")
    role_choice = input("请选择 [1]: ").strip() or "1"
    
    role_map = {
        "1": "viewer",
        "2": "editor",
        "3": "admin"
    }
    role = role_map.get(role_choice, "viewer")
    
    aliases_input = input("请输入用户别名（用逗号分隔，可选）: ").strip()
    aliases = [a.strip() for a in aliases_input.split(",") if a.strip()] if aliases_input else None
    
    # 创建用户
    success = create_user(token, new_username, new_password, role, aliases)
    
    # 3. 列出所有用户
    if success:
        list_users(token)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
