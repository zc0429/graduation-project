package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.dto.RoleRequest;
import com.example.wrongbook.entity.Role;
import com.example.wrongbook.entity.RolePermission;
import com.example.wrongbook.entity.UserRole;
import com.example.wrongbook.mapper.RoleMapper;
import com.example.wrongbook.mapper.RolePermissionMapper;
import com.example.wrongbook.mapper.UserRoleMapper;
import com.example.wrongbook.service.RoleService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;

@Service
@RequiredArgsConstructor
public class RoleServiceImpl implements RoleService {

    private final RoleMapper roleMapper;
    private final RolePermissionMapper rolePermissionMapper;
    private final UserRoleMapper userRoleMapper;

    @Override
    public Page<Role> page(Integer pageNum, Integer pageSize, String keyword) {
        LambdaQueryWrapper<Role> wrapper = new LambdaQueryWrapper<Role>()
                .and(StringUtils.hasText(keyword), w -> w
                        .like(Role::getRoleName, keyword)
                        .or().like(Role::getRoleKey, keyword))
                .orderByAsc(Role::getSort)
                .orderByAsc(Role::getId);
        return roleMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
    }

    @Override
    public Role get(Long id) {
        Role role = roleMapper.selectById(id);
        if (role == null) {
            throw new BizException("角色不存在");
        }
        return role;
    }

    @Override
    public Long add(RoleRequest request) {
        Long count = roleMapper.selectCount(
                new LambdaQueryWrapper<Role>().eq(Role::getRoleKey, request.getRoleKey()));
        if (count > 0) {
            throw new BizException("角色标识已存在");
        }
        Role role = new Role();
        copy(request, role);
        roleMapper.insert(role);
        return role.getId();
    }

    @Override
    public void update(Long id, RoleRequest request) {
        Role role = get(id);
        Long count = roleMapper.selectCount(new LambdaQueryWrapper<Role>()
                .eq(Role::getRoleKey, request.getRoleKey())
                .ne(Role::getId, id));
        if (count > 0) {
            throw new BizException("角色标识已存在");
        }
        copy(request, role);
        roleMapper.updateById(role);
    }

    @Override
    @Transactional
    public void remove(Long id) {
        get(id);
        Long used = userRoleMapper.selectCount(
                new LambdaQueryWrapper<UserRole>().eq(UserRole::getRoleId, id));
        if (used > 0) {
            throw new BizException("该角色已分配给用户，不能删除");
        }
        rolePermissionMapper.delete(
                new LambdaQueryWrapper<RolePermission>().eq(RolePermission::getRoleId, id));
        roleMapper.deleteById(id);
    }

    @Override
    public List<Long> listPermissionIds(Long roleId) {
        get(roleId);
        return rolePermissionMapper.selectList(
                        new LambdaQueryWrapper<RolePermission>().eq(RolePermission::getRoleId, roleId))
                .stream().map(RolePermission::getPermissionId).toList();
    }

    @Override
    @Transactional
    public void assignPermissions(Long roleId, List<Long> permissionIds) {
        get(roleId);
        rolePermissionMapper.delete(
                new LambdaQueryWrapper<RolePermission>().eq(RolePermission::getRoleId, roleId));
        if (permissionIds != null) {
            for (Long permissionId : permissionIds) {
                RolePermission rp = new RolePermission();
                rp.setRoleId(roleId);
                rp.setPermissionId(permissionId);
                rolePermissionMapper.insert(rp);
            }
        }
    }

    private void copy(RoleRequest request, Role role) {
        role.setRoleName(request.getRoleName());
        role.setRoleKey(request.getRoleKey());
        role.setSort(request.getSort() == null ? 0 : request.getSort());
        role.setStatus(request.getStatus() == null ? 1 : request.getStatus());
        role.setRemark(request.getRemark());
    }
}
