package com.example.wrongbook.service;

import com.example.wrongbook.dto.QuestionRecognitionRequest;
import com.example.wrongbook.vo.QuestionRecognitionResult;

public interface QuestionRecognitionService {

    QuestionRecognitionResult recognize(QuestionRecognitionRequest request);
}
