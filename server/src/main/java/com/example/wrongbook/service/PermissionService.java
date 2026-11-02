package com.example.wrongbook.service;

import com.example.wrongbook.dto.PermissionRequest;
import com.example.wrongbook.entity.Permission;

import java.util.List;

public interface PermissionService {

    /** 全部权限（按 sort、id 排序，前端可组装树） */
    List<Permission> list();

    Permission get(Long id);

    Long add(PermissionRequest request);

    void update(Long id, PermissionRequest request);

    void remove(Long id);
}
