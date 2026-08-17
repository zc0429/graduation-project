package com.example.wrongbook.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.ProfileUpdateRequest;
import com.example.wrongbook.entity.User;
import com.example.wrongbook.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/profile")
    public RestResponse<User> profile() {
        return RestResponse.ok(userService.getProfile());
    }

    @PutMapping("/profile")
    public RestResponse<Void> updateProfile(@Validated @RequestBody ProfileUpdateRequest request) {
        userService.updateProfile(request);
        return RestResponse.ok();
    }

    @GetMapping("/page")
    @RequireRole("admin")
    public RestResponse<Page<User>> page(@RequestParam(defaultValue = "1") Integer pageNum,
                                         @RequestParam(defaultValue = "10") Integer pageSize,
                                         @RequestParam(required = false) String role,
                                         @RequestParam(required = false) String keyword) {
        return RestResponse.ok(userService.page(pageNum, pageSize, role, keyword));
    }

    @DeleteMapping("/{id}")
    @RequireRole("admin")
    public RestResponse<Void> remove(@PathVariable Long id) {
        userService.removeUser(id);
        return RestResponse.ok();
    }
}
