package com.example.wrongbook.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.service.QuestionService;
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

@RestController
@RequestMapping("/api/question")
@RequiredArgsConstructor
public class QuestionController {

    private final QuestionService questionService;

    @PostMapping
    public RestResponse<Long> create(@Validated @RequestBody QuestionRequest request) {
        return RestResponse.ok(questionService.create(request));
    }

    @GetMapping("/page")
    public RestResponse<Page<Question>> page(@RequestParam(defaultValue = "1") Integer pageNum,
                                             @RequestParam(defaultValue = "10") Integer pageSize,
                                             @RequestParam(required = false) Long subjectId,
                                             @RequestParam(required = false) Long knowledgePointId) {
        return RestResponse.ok(questionService.page(pageNum, pageSize, subjectId, knowledgePointId));
    }

    @GetMapping("/{id}")
    public RestResponse<Question> detail(@PathVariable Long id) {
        return RestResponse.ok(questionService.detail(id));
    }

    @PutMapping("/{id}")
    public RestResponse<Void> update(@PathVariable Long id, @Validated @RequestBody QuestionRequest request) {
        questionService.update(id, request);
        return RestResponse.ok();
    }

    @DeleteMapping("/{id}")
    public RestResponse<Void> remove(@PathVariable Long id) {
        questionService.remove(id);
        return RestResponse.ok();
    }
}
