package com.example.wrongbook.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.dto.UserRoleRequest;
import com.example.wrongbook.entity.UserRole;

import java.util.List;

public interface UserRoleService {

    Page<UserRole> page(Integer pageNum, Integer pageSize, Long userId, Long roleId);

    Long add(UserRoleRequest request);

    void remove(Long id);

    /** 查询某用户已分配的角色 ID 列表 */
    List<Long> listRoleIds(Long userId);

    /** 给用户重新分配角色（先删后插，事务） */
    void assignRoles(Long userId, List<Long> roleIds);
}
