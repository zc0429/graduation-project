package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.dto.LoginRequest;
import com.example.wrongbook.dto.RegisterRequest;
import com.example.wrongbook.entity.User;
import com.example.wrongbook.mapper.UserMapper;
import com.example.wrongbook.service.AuthService;
import com.example.wrongbook.util.JwtUtil;
import com.example.wrongbook.vo.LoginResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    /** BCryptPasswordEncoder 无状态且线程安全 */
    private static final BCryptPasswordEncoder ENCODER = new BCryptPasswordEncoder();

    private final UserMapper userMapper;
    private final JwtUtil jwtUtil;

    @Override
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
        return user.getId();
    }

    @Override
    public LoginResponse login(LoginRequest request) {
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, request.getUsername()));
        if (user == null || !ENCODER.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ResultCode.UNAUTHORIZED.getCode(), "用户名或密码错误");
        }
        return new LoginResponse(jwtUtil.createToken(user.getId(), user.getRole()), user);
    }
}
