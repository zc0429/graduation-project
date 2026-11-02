package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.dto.PermissionRequest;
import com.example.wrongbook.entity.Permission;
import com.example.wrongbook.entity.RolePermission;
import com.example.wrongbook.mapper.PermissionMapper;
import com.example.wrongbook.mapper.RolePermissionMapper;
import com.example.wrongbook.service.PermissionService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PermissionServiceImpl implements PermissionService {

    private final PermissionMapper permissionMapper;
    private final RolePermissionMapper rolePermissionMapper;

    @Override
    public List<Permission> list() {
        return permissionMapper.selectList(new LambdaQueryWrapper<Permission>()
                .orderByAsc(Permission::getSort)
                .orderByAsc(Permission::getId));
    }

    @Override
    public Permission get(Long id) {
        Permission permission = permissionMapper.selectById(id);
        if (permission == null) {
            throw new BizException("权限不存在");
        }
        return permission;
    }

    @Override
    public Long add(PermissionRequest request) {
        Long count = permissionMapper.selectCount(
                new LambdaQueryWrapper<Permission>().eq(Permission::getPermissionKey, request.getPermissionKey()));
        if (count > 0) {
            throw new BizException("权限码已存在");
        }
        Permission permission = new Permission();
        copy(request, permission);
        permissionMapper.insert(permission);
        return permission.getId();
    }

    @Override
    public void update(Long id, PermissionRequest request) {
        Permission permission = get(id);
        Long count = permissionMapper.selectCount(new LambdaQueryWrapper<Permission>()
                .eq(Permission::getPermissionKey, request.getPermissionKey())
                .ne(Permission::getId, id));
        if (count > 0) {
            throw new BizException("权限码已存在");
        }
        copy(request, permission);
        permissionMapper.updateById(permission);
    }

    @Override
    @Transactional
    public void remove(Long id) {
        get(id);
        Long children = permissionMapper.selectCount(
                new LambdaQueryWrapper<Permission>().eq(Permission::getParentId, id));
        if (children > 0) {
            throw new BizException("该权限下还有子权限，不能删除");
        }
        rolePermissionMapper.delete(
                new LambdaQueryWrapper<RolePermission>().eq(RolePermission::getPermissionId, id));
        permissionMapper.deleteById(id);
    }

    private void copy(PermissionRequest request, Permission permission) {
        permission.setParentId(request.getParentId() == null ? 0L : request.getParentId());
        permission.setName(request.getName());
        permission.setPermissionKey(request.getPermissionKey());
        permission.setType(request.getType() == null ? "button" : request.getType());
        permission.setPath(request.getPath());
        permission.setSort(request.getSort() == null ? 0 : request.getSort());
        permission.setStatus(request.getStatus() == null ? 1 : request.getStatus());
    }
}
