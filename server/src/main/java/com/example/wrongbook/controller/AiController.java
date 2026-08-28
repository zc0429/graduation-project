package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.entity.AiAnalysis;
import com.example.wrongbook.service.AiAnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/ai")
@RequiredArgsConstructor
@RequireRole("student")
public class AiController {

    private final AiAnalysisService aiAnalysisService;

    /** 触发 AI 解析（异步，立即返回受理结果） */
    @PostMapping("/analyze/{questionId}")
    public RestResponse<Void> analyze(@PathVariable Long questionId) {
        aiAnalysisService.trigger(questionId);
        return RestResponse.ok();
    }

    /** 查询解析结果（前端轮询） */
    @GetMapping("/analysis/{questionId}")
    public RestResponse<AiAnalysis> analysis(@PathVariable Long questionId) {
        return RestResponse.ok(aiAnalysisService.getByQuestion(questionId));
    }
}
