package com.example.wrongbook.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.dto.RolePermissionRequest;
import com.example.wrongbook.entity.RolePermission;

public interface RolePermissionService {

    Page<RolePermission> page(Integer pageNum, Integer pageSize, Long roleId, Long permissionId);

    Long add(RolePermissionRequest request);

    void remove(Long id);
}
