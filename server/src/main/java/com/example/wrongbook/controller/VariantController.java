package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.service.VariantService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/variant")
@RequiredArgsConstructor
@RequireRole("student")
public class VariantController {

    private final VariantService variantService;

    @PostMapping("/generate/{questionId}")
    public RestResponse<List<VariantQuestion>> generate(@PathVariable Long questionId) {
        return RestResponse.ok(variantService.generate(questionId));
    }

    @GetMapping("/list")
    public RestResponse<List<VariantQuestion>> list(@RequestParam Long questionId) {
        return RestResponse.ok(variantService.list(questionId));
    }
}
