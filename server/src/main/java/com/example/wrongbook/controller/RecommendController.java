package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.service.RecommendService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/recommend")
@RequiredArgsConstructor
@RequireRole("student")
public class RecommendController {

    private final RecommendService recommendService;

    @GetMapping("/similar")
    public RestResponse<List<Question>> similar(@RequestParam Long questionId) {
        return RestResponse.ok(recommendService.similar(questionId));
    }
}
