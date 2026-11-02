package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.dto.LoginRequest;
import com.example.wrongbook.dto.RegisterRequest;
import cn.dev33.satoken.stp.StpUtil;
import com.example.wrongbook.entity.Role;
import com.example.wrongbook.entity.User;
import com.example.wrongbook.entity.UserRole;
import com.example.wrongbook.mapper.RoleMapper;
import com.example.wrongbook.mapper.UserMapper;
import com.example.wrongbook.mapper.UserRoleMapper;
import com.example.wrongbook.service.AuthService;
import com.example.wrongbook.vo.LoginResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    /** BCryptPasswordEncoder 无状态且线程安全 */
    private static final BCryptPasswordEncoder ENCODER = new BCryptPasswordEncoder();

    private final UserMapper userMapper;
    private final RoleMapper roleMapper;
    private final UserRoleMapper userRoleMapper;

    @Override
    @Transactional
    public Long register(RegisterRequest request) {
        Long count = userMapper.selectCount(
                new LambdaQueryWrapper<User>().eq(User::getUsername, request.getUsername()));
        if (count > 0) {
            throw new BizException("用户名已存在");
        }
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(ENCODER.encode(request.getPassword()));
        user.setNickname(StringUtils.hasText(request.getNickname()) ? request.getNickname() : request.getUsername());
        user.setRole("student");
        userMapper.insert(user);
        // 同步登记 RBAC 用户-角色关联（student 角色），与 user.role 字段保持一致
        Role student = roleMapper.selectOne(
                new LambdaQueryWrapper<Role>().eq(Role::getRoleKey, "student"));
        if (student != null) {
            UserRole userRole = new UserRole();
            userRole.setUserId(user.getId());
            userRole.setRoleId(student.getId());
            userRoleMapper.insert(userRole);
        }
        return user.getId();
    }

    @Override
    public LoginResponse login(LoginRequest request) {
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, request.getUsername()));
        if (user == null || !ENCODER.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ResultCode.UNAUTHORIZED.getCode(), "用户名或密码错误");
        }
        // 实训改造：登录会话由 Sa-Token 管理（原 JWT 已下线），返回的 token 仍按 Bearer 方式传递
        StpUtil.login(user.getId());
        return new LoginResponse(StpUtil.getTokenValue(), user);
    }
}
