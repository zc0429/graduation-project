package com.example.wrongbook.service;
import com.example.wrongbook.vo.LearningContentVO;
import com.example.wrongbook.vo.PracticeResourceVO;
import com.example.wrongbook.vo.PracticeProgressVO;
public interface LearningService {
    LearningContentVO knowledge(Long questionId);
    PracticeResourceVO nextPractice(Long questionId);
    PracticeProgressVO progress(Long questionId);
}
