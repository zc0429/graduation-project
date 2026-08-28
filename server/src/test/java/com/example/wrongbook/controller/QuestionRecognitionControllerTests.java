package com.example.wrongbook.controller;

import com.example.wrongbook.common.GlobalExceptionHandler;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.config.AuthInterceptor;
import com.example.wrongbook.entity.User;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.PracticeRecordMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.mapper.UserMapper;
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
    private final UserMapper userMapper = mock(UserMapper.class);
    private final QuestionMapper questionMapper = mock(QuestionMapper.class);
    private final ReviewPlanMapper reviewPlanMapper = mock(ReviewPlanMapper.class);
    private final AiAnalysisMapper aiAnalysisMapper = mock(AiAnalysisMapper.class);
    private final VariantQuestionMapper variantQuestionMapper = mock(VariantQuestionMapper.class);
    private final PracticeRecordMapper practiceRecordMapper = mock(PracticeRecordMapper.class);
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        ObjectMapper objectMapper = new ObjectMapper();
        AuthInterceptor authInterceptor = new AuthInterceptor(jwtUtil, userMapper, objectMapper);
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
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value(401));

        verifyNoInteractions(recognitionService);
    }

    @Test
    void authenticatedRecognitionReturnsTemporaryResultWithoutBusinessWrites() throws Exception {
        when(jwtUtil.parse("valid-token")).thenReturn(new LoginUser(7L, "student"));
        when(userMapper.selectById(7L)).thenReturn(user(7L, "student", 1));
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

    @Test
    void rejectsDisabledAccountEvenWhenItsTokenIsStillCryptographicallyValid() throws Exception {
        when(jwtUtil.parse("disabled-token")).thenReturn(new LoginUser(7L, "student"));
        when(userMapper.selectById(7L)).thenReturn(user(7L, "student", 0));

        mockMvc.perform(post("/api/question-recognition/recognize")
                        .header("Authorization", "Bearer disabled-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"imageBase64\":\"data:image/png;base64,iVBORw0KGgo=\"}"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value(401));

        verifyNoInteractions(recognitionService);
    }

    @Test
    void usesCurrentDatabaseRoleInsteadOfStaleTokenRole() throws Exception {
        when(jwtUtil.parse("stale-role-token")).thenReturn(new LoginUser(8L, "student"));
        when(userMapper.selectById(8L)).thenReturn(user(8L, "teacher", 1));

        mockMvc.perform(post("/api/question-recognition/recognize")
                        .header("Authorization", "Bearer stale-role-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"imageBase64\":\"data:image/png;base64,iVBORw0KGgo=\"}"))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));

        verifyNoInteractions(recognitionService);
    }

    @Test
    void businessErrorsUseMatchingHttpStatus() throws Exception {
        when(jwtUtil.parse("valid-token")).thenReturn(new LoginUser(7L, "student"));
        when(userMapper.selectById(7L)).thenReturn(user(7L, "student", 1));
        when(recognitionService.recognize(any()))
                .thenThrow(new BizException(ResultCode.BAD_REQUEST.getCode(), "图片无效"));

        mockMvc.perform(post("/api/question-recognition/recognize")
                        .header("Authorization", "Bearer valid-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"imageBase64\":\"data:image/png;base64,iVBORw0KGgo=\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(400));
    }

    private User user(Long id, String role, int status) {
        User user = new User();
        user.setId(id);
        user.setRole(role);
        user.setStatus(status);
        return user;
    }
}
