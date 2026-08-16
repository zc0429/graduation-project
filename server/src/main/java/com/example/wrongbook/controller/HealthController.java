package com.example.wrongbook.controller;

import com.example.wrongbook.common.RestResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class HealthController {

    @GetMapping("/health")
    public RestResponse<Map<String, String>> health() {
        return RestResponse.ok(Map.of("status", "ok"));
    }
}
