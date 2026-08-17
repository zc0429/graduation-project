package com.example.wrongbook.service;

import com.example.wrongbook.dto.LoginRequest;
import com.example.wrongbook.dto.RegisterRequest;
import com.example.wrongbook.vo.LoginResponse;

public interface AuthService {

    /** 用户注册（角色固定为学生），返回用户 ID */
    Long register(RegisterRequest request);

    /** 用户登录，返回 JWT 与用户信息 */
    LoginResponse login(LoginRequest request);
}
