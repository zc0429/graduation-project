package com.example.wrongbook.controller;

import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.LoginRequest;
import com.example.wrongbook.dto.RegisterRequest;
import com.example.wrongbook.service.AuthService;
import com.example.wrongbook.vo.LoginResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public RestResponse<Long> register(@Validated @RequestBody RegisterRequest request) {
        return RestResponse.ok(authService.register(request));
    }

    @PostMapping("/login")
    public RestResponse<LoginResponse> login(@Validated @RequestBody LoginRequest request) {
        return RestResponse.ok(authService.login(request));
    }
}
