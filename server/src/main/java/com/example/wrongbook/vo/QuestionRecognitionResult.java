package com.example.wrongbook.vo;

import lombok.AllArgsConstructor;
import lombok.Getter;

/** 图片识别的临时结果；不会直接持久化为 Question。 */
@Getter
@AllArgsConstructor
public class QuestionRecognitionResult {

    private Long subjectId;
    private String subjectName;
    private String stem;
    private String studentAnswer;
    private String source;
}
