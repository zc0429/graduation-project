package com.example.wrongbook.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.dto.ProfileUpdateRequest;
import com.example.wrongbook.entity.User;

public interface UserService {

    /** 查询当前登录用户个人信息 */
    User getProfile();

    /** 修改当前登录用户个人信息（昵称/邮箱/班级） */
    void updateProfile(ProfileUpdateRequest request);

    /** 用户分页查询（管理员） */
    Page<User> page(Integer pageNum, Integer pageSize, String role, String keyword);

    /** 注销用户（管理员，逻辑删除即停用） */
    void removeUser(Long id);
}
