package com.example.wrongbook.controller;

import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.dto.QuestionRecognitionRequest;
import com.example.wrongbook.service.QuestionRecognitionService;
import com.example.wrongbook.vo.QuestionRecognitionResult;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/question-recognition")
@RequiredArgsConstructor
public class QuestionRecognitionController {

    private final QuestionRecognitionService questionRecognitionService;

    @PostMapping("/recognize")
    public RestResponse<QuestionRecognitionResult> recognize(
            @Validated @RequestBody QuestionRecognitionRequest request) {
        return RestResponse.ok(questionRecognitionService.recognize(request));
    }
}
