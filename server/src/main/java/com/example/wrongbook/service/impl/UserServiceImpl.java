package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.ProfileUpdateRequest;
import com.example.wrongbook.entity.User;
import com.example.wrongbook.mapper.UserMapper;
import com.example.wrongbook.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;

    @Override
    public User getProfile() {
        User user = userMapper.selectById(UserContext.getUserId());
        if (user == null) {
            throw new BizException(ResultCode.NOT_FOUND.getCode(), "用户不存在");
        }
        return user;
    }

    @Override
    public void updateProfile(ProfileUpdateRequest request) {
        User user = new User();
        user.setId(UserContext.getUserId());
        user.setNickname(request.getNickname());
        user.setEmail(request.getEmail());
        user.setClassName(request.getClassName());
        userMapper.updateById(user);
    }

    @Override
    public Page<User> page(Integer pageNum, Integer pageSize, String role, String keyword) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StringUtils.hasText(role), User::getRole, role)
                .and(StringUtils.hasText(keyword), w -> w.like(User::getUsername, keyword)
                        .or().like(User::getNickname, keyword))
                .orderByAsc(User::getId);
        return userMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
    }

    @Override
    public void removeUser(Long id) {
        if (id.equals(UserContext.getUserId())) {
            throw new BizException("不能注销当前登录账号");
        }
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BizException(ResultCode.NOT_FOUND.getCode(), "用户不存在");
        }
        userMapper.deleteById(id);
    }
}
