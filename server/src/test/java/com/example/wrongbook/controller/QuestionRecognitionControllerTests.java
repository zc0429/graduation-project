package com.example.wrongbook.controller;

import com.example.wrongbook.common.GlobalExceptionHandler;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.config.AuthInterceptor;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.PracticeRecordMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.QuestionRecognitionService;
import com.example.wrongbook.util.JwtUtil;
import com.example.wrongbook.vo.QuestionRecognitionResult;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.setup.MockMvcBuilders.standaloneSetup;

class QuestionRecognitionControllerTests {

    private final QuestionRecognitionService recognitionService = mock(QuestionRecognitionService.class);
    private final JwtUtil jwtUtil = mock(JwtUtil.class);
    private final QuestionMapper questionMapper = mock(QuestionMapper.class);
    private final ReviewPlanMapper reviewPlanMapper = mock(ReviewPlanMapper.class);
    private final AiAnalysisMapper aiAnalysisMapper = mock(AiAnalysisMapper.class);
    private final VariantQuestionMapper variantQuestionMapper = mock(VariantQuestionMapper.class);
    private final PracticeRecordMapper practiceRecordMapper = mock(PracticeRecordMapper.class);
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        ObjectMapper objectMapper = new ObjectMapper();
        AuthInterceptor authInterceptor = new AuthInterceptor(jwtUtil, objectMapper);
        mockMvc = standaloneSetup(new QuestionRecognitionController(recognitionService))
                .addInterceptors(authInterceptor)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void requiresAuthentication() throws Exception {
        mockMvc.perform(post("/api/question-recognition/recognize")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"imageBase64\":\"data:image/png;base64,iVBORw0KGgo=\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(401));

        verifyNoInteractions(recognitionService);
    }

    @Test
    void authenticatedRecognitionReturnsTemporaryResultWithoutBusinessWrites() throws Exception {
        when(jwtUtil.parse("valid-token")).thenReturn(new LoginUser(7L, "student"));
        when(recognitionService.recognize(any())).thenReturn(new QuestionRecognitionResult(
                1L, "数学", "一道题", "学生作答", "课堂练习"));

        mockMvc.perform(post("/api/question-recognition/recognize")
                        .header("Authorization", "Bearer valid-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"imageBase64\":\"data:image/png;base64,iVBORw0KGgo=\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.subjectId").value(1))
                .andExpect(jsonPath("$.data.studentAnswer").value("学生作答"));

        verify(recognitionService).recognize(any());
        verifyNoInteractions(questionMapper, reviewPlanMapper, aiAnalysisMapper,
                variantQuestionMapper, practiceRecordMapper);
    }
}
