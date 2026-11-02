package com.example.wrongbook.config;

import cn.dev33.satoken.stp.StpInterface;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.entity.Permission;
import com.example.wrongbook.entity.Role;
import com.example.wrongbook.entity.RolePermission;
import com.example.wrongbook.entity.User;
import com.example.wrongbook.entity.UserRole;
import com.example.wrongbook.mapper.PermissionMapper;
import com.example.wrongbook.mapper.RoleMapper;
import com.example.wrongbook.mapper.RolePermissionMapper;
import com.example.wrongbook.mapper.UserMapper;
import com.example.wrongbook.mapper.UserRoleMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Sa-Token 权限数据源：根据登录用户 ID，从 RBAC 五表查询其角色与权限码。
 * 关系链：user → user_role → role → role_permission → permission。
 * 另外把 user.role 字段对应的角色并入结果，保证与既有 @RequireRole 校验口径一致
 * （存量账号即使尚未在 user_role 中登记，也不会因此丢权限）。
 */
@Component
@RequiredArgsConstructor
public class StpInterfaceImpl implements StpInterface {

    private final UserMapper userMapper;
    private final UserRoleMapper userRoleMapper;
    private final RoleMapper roleMapper;
    private final RolePermissionMapper rolePermissionMapper;
    private final PermissionMapper permissionMapper;

    @Override
    public List<String> getRoleList(Object loginId, String loginType) {
        return new ArrayList<>(loadRoleKeys(loginId));
    }

    @Override
    public List<String> getPermissionList(Object loginId, String loginType) {
        Set<String> keys = new LinkedHashSet<>();
        Set<Long> roleIds = loadRoleIds(loginId);
        if (roleIds.isEmpty()) {
            return new ArrayList<>();
        }
        List<RolePermission> relations = rolePermissionMapper.selectList(
                new LambdaQueryWrapper<RolePermission>().in(RolePermission::getRoleId, roleIds));
        Set<Long> permissionIds = new LinkedHashSet<>();
        for (RolePermission relation : relations) {
            permissionIds.add(relation.getPermissionId());
        }
        if (permissionIds.isEmpty()) {
            return new ArrayList<>();
        }
        List<Permission> permissions = permissionMapper.selectList(new LambdaQueryWrapper<Permission>()
                .in(Permission::getId, permissionIds)
                .eq(Permission::getStatus, 1));
        for (Permission permission : permissions) {
            keys.add(permission.getPermissionKey());
        }
        return new ArrayList<>(keys);
    }

    /** 用户的全部角色 ID：user_role 登记 + user.role 字段对应的角色 */
    private Set<Long> loadRoleIds(Object loginId) {
        Set<Long> roleIds = new LinkedHashSet<>();
        Long userId = toLong(loginId);
        if (userId == null) {
            return roleIds;
        }
        for (UserRole userRole : userRoleMapper.selectList(
                new LambdaQueryWrapper<UserRole>().eq(UserRole::getUserId, userId))) {
            roleIds.add(userRole.getRoleId());
        }
        User user = userMapper.selectById(userId);
        if (user != null && user.getRole() != null) {
            Role byKey = roleMapper.selectOne(
                    new LambdaQueryWrapper<Role>().eq(Role::getRoleKey, user.getRole()));
            if (byKey != null) {
                roleIds.add(byKey.getId());
            }
        }
        return roleIds;
    }

    private Set<String> loadRoleKeys(Object loginId) {
        Set<String> keys = new LinkedHashSet<>();
        Long userId = toLong(loginId);
        if (userId == null) {
            return keys;
        }
        for (Long roleId : loadRoleIds(loginId)) {
            Role role = roleMapper.selectById(roleId);
            if (role != null && Integer.valueOf(1).equals(role.getStatus())) {
                keys.add(role.getRoleKey());
            }
        }
        User user = userMapper.selectById(userId);
        if (user != null && user.getRole() != null) {
            keys.add(user.getRole());
        }
        return keys;
    }

    private Long toLong(Object loginId) {
        if (loginId == null) {
            return null;
        }
        try {
            return Long.valueOf(String.valueOf(loginId));
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
