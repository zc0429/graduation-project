package com.example.wrongbook.common;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * 当前登录用户信息（由 JWT 解析而来）
 */
@Data
@AllArgsConstructor
public class LoginUser {

    private Long id;

    /** 角色：student/teacher/admin */
    private String role;
}
