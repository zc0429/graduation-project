package com.example.wrongbook.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.PracticeRequest;
import com.example.wrongbook.entity.PracticeRecord;
import com.example.wrongbook.service.PracticeService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/practice")
@RequiredArgsConstructor
@RequireRole("student")
public class PracticeController {

    private final PracticeService practiceService;

    @PostMapping
    public RestResponse<Long> submit(@Validated @RequestBody PracticeRequest request) {
        return RestResponse.ok(practiceService.submit(request));
    }

    @GetMapping("/page")
    public RestResponse<Page<PracticeRecord>> page(@RequestParam(defaultValue = "1") Integer pageNum,
                                                   @RequestParam(defaultValue = "10") Integer pageSize) {
        return RestResponse.ok(practiceService.page(pageNum, pageSize));
    }
}
