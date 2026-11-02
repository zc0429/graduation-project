package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.dto.UserRoleRequest;
import com.example.wrongbook.entity.UserRole;
import com.example.wrongbook.mapper.RoleMapper;
import com.example.wrongbook.mapper.UserMapper;
import com.example.wrongbook.mapper.UserRoleMapper;
import com.example.wrongbook.service.UserRoleService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserRoleServiceImpl implements UserRoleService {

    private final UserRoleMapper userRoleMapper;
    private final UserMapper userMapper;
    private final RoleMapper roleMapper;

    @Override
    public Page<UserRole> page(Integer pageNum, Integer pageSize, Long userId, Long roleId) {
        LambdaQueryWrapper<UserRole> wrapper = new LambdaQueryWrapper<UserRole>()
                .eq(userId != null, UserRole::getUserId, userId)
                .eq(roleId != null, UserRole::getRoleId, roleId)
                .orderByAsc(UserRole::getId);
        return userRoleMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
    }

    @Override
    public Long add(UserRoleRequest request) {
        checkUserAndRole(request.getUserId(), request.getRoleId());
        Long count = userRoleMapper.selectCount(new LambdaQueryWrapper<UserRole>()
                .eq(UserRole::getUserId, request.getUserId())
                .eq(UserRole::getRoleId, request.getRoleId()));
        if (count > 0) {
            throw new BizException("该用户已拥有此角色");
        }
        UserRole userRole = new UserRole();
        userRole.setUserId(request.getUserId());
        userRole.setRoleId(request.getRoleId());
        userRoleMapper.insert(userRole);
        return userRole.getId();
    }

    @Override
    public void remove(Long id) {
        if (userRoleMapper.selectById(id) == null) {
            throw new BizException("用户角色关联不存在");
        }
        userRoleMapper.deleteById(id);
    }

    @Override
    public List<Long> listRoleIds(Long userId) {
        return userRoleMapper.selectList(
                        new LambdaQueryWrapper<UserRole>().eq(UserRole::getUserId, userId))
                .stream().map(UserRole::getRoleId).toList();
    }

    @Override
    @Transactional
    public void assignRoles(Long userId, List<Long> roleIds) {
        if (userMapper.selectById(userId) == null) {
            throw new BizException("用户不存在");
        }
        userRoleMapper.delete(new LambdaQueryWrapper<UserRole>().eq(UserRole::getUserId, userId));
        if (roleIds != null) {
            for (Long roleId : roleIds) {
                if (roleMapper.selectById(roleId) == null) {
                    throw new BizException("角色不存在：" + roleId);
                }
                UserRole userRole = new UserRole();
                userRole.setUserId(userId);
                userRole.setRoleId(roleId);
                userRoleMapper.insert(userRole);
            }
        }
    }

    private void checkUserAndRole(Long userId, Long roleId) {
        if (userMapper.selectById(userId) == null) {
            throw new BizException("用户不存在");
        }
        if (roleMapper.selectById(roleId) == null) {
            throw new BizException("角色不存在");
        }
    }
}
