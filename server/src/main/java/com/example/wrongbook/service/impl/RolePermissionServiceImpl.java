package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.dto.RolePermissionRequest;
import com.example.wrongbook.entity.RolePermission;
import com.example.wrongbook.mapper.PermissionMapper;
import com.example.wrongbook.mapper.RoleMapper;
import com.example.wrongbook.mapper.RolePermissionMapper;
import com.example.wrongbook.service.RolePermissionService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RolePermissionServiceImpl implements RolePermissionService {

    private final RolePermissionMapper rolePermissionMapper;
    private final RoleMapper roleMapper;
    private final PermissionMapper permissionMapper;

    @Override
    public Page<RolePermission> page(Integer pageNum, Integer pageSize, Long roleId, Long permissionId) {
        LambdaQueryWrapper<RolePermission> wrapper = new LambdaQueryWrapper<RolePermission>()
                .eq(roleId != null, RolePermission::getRoleId, roleId)
                .eq(permissionId != null, RolePermission::getPermissionId, permissionId)
                .orderByAsc(RolePermission::getId);
        return rolePermissionMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
    }

    @Override
    public Long add(RolePermissionRequest request) {
        if (roleMapper.selectById(request.getRoleId()) == null) {
            throw new BizException("角色不存在");
        }
        if (permissionMapper.selectById(request.getPermissionId()) == null) {
            throw new BizException("权限不存在");
        }
        Long count = rolePermissionMapper.selectCount(new LambdaQueryWrapper<RolePermission>()
                .eq(RolePermission::getRoleId, request.getRoleId())
                .eq(RolePermission::getPermissionId, request.getPermissionId()));
        if (count > 0) {
            throw new BizException("该角色已拥有此权限");
        }
        RolePermission rp = new RolePermission();
        rp.setRoleId(request.getRoleId());
        rp.setPermissionId(request.getPermissionId());
        rolePermissionMapper.insert(rp);
        return rp.getId();
    }

    @Override
    public void remove(Long id) {
        if (rolePermissionMapper.selectById(id) == null) {
            throw new BizException("角色权限关联不存在");
        }
        rolePermissionMapper.deleteById(id);
    }
}
