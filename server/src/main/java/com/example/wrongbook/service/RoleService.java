package com.example.wrongbook.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.dto.RoleRequest;
import com.example.wrongbook.entity.Role;

import java.util.List;

public interface RoleService {

    /** 分页查询角色（可按名称/标识关键字模糊查） */
    Page<Role> page(Integer pageNum, Integer pageSize, String keyword);

    Role get(Long id);

    Long add(RoleRequest request);

    void update(Long id, RoleRequest request);

    void remove(Long id);

    /** 查询某角色已分配的权限 ID 列表 */
    List<Long> listPermissionIds(Long roleId);

    /** 给角色重新分配权限（先删后插，事务） */
    void assignPermissions(Long roleId, List<Long> permissionIds);
}
