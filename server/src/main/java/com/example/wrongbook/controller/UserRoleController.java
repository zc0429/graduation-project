package com.example.wrongbook.controller;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.AssignIdsRequest;
import com.example.wrongbook.dto.UserRoleRequest;
import com.example.wrongbook.entity.UserRole;
import com.example.wrongbook.service.UserRoleService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 用户-角色关联管理（实训 RBAC 模块）：关联 CRUD + 给用户批量分配角色。
 */
@RestController
@RequestMapping("/api/system/user-role")
@RequiredArgsConstructor
@RequireRole("admin")
public class UserRoleController {

    private final UserRoleService userRoleService;

    @GetMapping("/page")
    @SaCheckPermission("system:user:list")
    public RestResponse<Page<UserRole>> page(@RequestParam(defaultValue = "1") Integer pageNum,
                                             @RequestParam(defaultValue = "10") Integer pageSize,
                                             @RequestParam(required = false) Long userId,
                                             @RequestParam(required = false) Long roleId) {
        return RestResponse.ok(userRoleService.page(pageNum, pageSize, userId, roleId));
    }

    @PostMapping
    @SaCheckPermission("system:user:edit")
    public RestResponse<Long> add(@Validated @RequestBody UserRoleRequest request) {
        return RestResponse.ok(userRoleService.add(request));
    }

    @DeleteMapping("/{id}")
    @SaCheckPermission("system:user:edit")
    public RestResponse<Void> remove(@PathVariable Long id) {
        userRoleService.remove(id);
        return RestResponse.ok();
    }

    @GetMapping("/user/{userId}")
    @SaCheckPermission("system:user:list")
    public RestResponse<List<Long>> roleIds(@PathVariable Long userId) {
        return RestResponse.ok(userRoleService.listRoleIds(userId));
    }

    @PutMapping("/user/{userId}")
    @SaCheckPermission("system:user:edit")
    public RestResponse<Void> assignRoles(@PathVariable Long userId, @RequestBody AssignIdsRequest request) {
        userRoleService.assignRoles(userId, request.getIds());
        return RestResponse.ok();
    }
}
