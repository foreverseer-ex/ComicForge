/**
 * 初始化管理员账号脚本
 * 
 * 首次运行时创建默认管理员账号
 */

import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

async function initAdmin() {
  try {
    // 检查是否已有用户
    const userCount = await prisma.user.count();
    if (userCount > 0) {
      console.log('Users already exist, skipping admin initialization');
      return;
    }

    // 创建默认管理员
    const defaultPassword = 'admin123'; // 首次登录后应修改
    const hashedPassword = await hashPassword(defaultPassword);

    const admin = await prisma.user.create({
      data: {
        username: 'admin',
        password: hashedPassword,
        isAdmin: true,
      },
    });

    console.log('Admin user created:');
    console.log('Username: admin');
    console.log('Password: admin123');
    console.log('Please change the password after first login!');
  } catch (error) {
    console.error('Failed to initialize admin:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

initAdmin();
