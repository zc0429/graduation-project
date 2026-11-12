package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.service.LearningService;
import com.example.wrongbook.vo.LearningContentVO;
import com.example.wrongbook.vo.PracticeResourceVO;
import com.example.wrongbook.vo.PracticeProgressVO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/learning")
@RequireRole("student")
@RequiredArgsConstructor
public class LearningController {
    private final LearningService learningService;
    @PostMapping("/knowledge/{questionId}")
    public RestResponse<LearningContentVO> knowledge(@PathVariable Long questionId) {
        return RestResponse.ok(learningService.knowledge(questionId));
    }
    @PostMapping("/practice/next/{questionId}")
    public RestResponse<PracticeResourceVO> nextPractice(@PathVariable Long questionId) {
        return RestResponse.ok(learningService.nextPractice(questionId));
    }
    @GetMapping("/practice/progress/{questionId}")
    public RestResponse<PracticeProgressVO> progress(@PathVariable Long questionId) {
        return RestResponse.ok(learningService.progress(questionId));
    }
}
