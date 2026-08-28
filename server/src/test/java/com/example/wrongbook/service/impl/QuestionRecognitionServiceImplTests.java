package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.config.ImageRecognitionProperties;
import com.example.wrongbook.dto.QuestionRecognitionRequest;
import com.example.wrongbook.entity.Subject;
import com.example.wrongbook.service.QuestionRecognitionClient;
import com.example.wrongbook.service.SubjectService;
import com.example.wrongbook.vo.QuestionRecognitionResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.ObjectProvider;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class QuestionRecognitionServiceImplTests {

    private static final String VALID_PNG = "data:image/png;base64,iVBORw0KGgo=";

    private final ImageRecognitionProperties properties = new ImageRecognitionProperties();
    private final QuestionRecognitionClient client = mock(QuestionRecognitionClient.class);
    private final SubjectService subjectService = mock(SubjectService.class);
    @SuppressWarnings("unchecked")
    private final ObjectProvider<QuestionRecognitionClient> clientProvider = mock(ObjectProvider.class);
    private QuestionRecognitionServiceImpl service;

    @BeforeEach
    void setUp() {
        properties.setEnabled(true);
        when(clientProvider.getIfAvailable()).thenReturn(client);
        when(subjectService.list()).thenReturn(List.of(subject(1L, "数学"), subject(2L, "物理")));
        service = new QuestionRecognitionServiceImpl(properties, clientProvider, subjectService);
    }

    @Test
    void mapsOnlyAnExistingSubjectAndKeepsStudentAnswerTransient() {
        when(client.recognize(VALID_PNG, List.of("数学", "物理")))
                .thenReturn(new QuestionRecognitionClient.Extraction(
                        "数学", "一道数学题", "学生写了 x=3", "课堂练习"));

        QuestionRecognitionResult result = service.recognize(request(VALID_PNG));

        assertThat(result.getSubjectId()).isEqualTo(1L);
        assertThat(result.getSubjectName()).isEqualTo("数学");
        assertThat(result.getStem()).isEqualTo("一道数学题");
        assertThat(result.getStudentAnswer()).isEqualTo("学生写了 x=3");
        assertThat(result.getSource()).isEqualTo("课堂练习");
    }

    @Test
    void discardsSubjectNameOutsideCurrentCandidates() {
        when(client.recognize(anyString(), anyList()))
                .thenReturn(new QuestionRecognitionClient.Extraction(
                        "计算机科学", "一道可见题目", null, null));

        QuestionRecognitionResult result = service.recognize(request(VALID_PNG));

        assertThat(result.getSubjectId()).isNull();
        assertThat(result.getSubjectName()).isNull();
        assertThat(result.getStem()).isEqualTo("一道可见题目");
    }

    @Test
    void disabledModeFailsBeforeSubjectLookupOrNetworkCall() {
        properties.setEnabled(false);

        assertThatThrownBy(() -> service.recognize(request(VALID_PNG)))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("未启用");
        verify(subjectService, never()).list();
        verify(client, never()).recognize(anyString(), anyList());
    }

    @Test
    void rejectsUnsupportedInvalidAndSpoofedImagesBeforeNetworkCall() {
        assertThatThrownBy(() -> service.recognize(request("data:image/gif;base64,R0lGODlh")))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("JPG、PNG 或 WebP");
        assertThatThrownBy(() -> service.recognize(request("data:image/png;base64,%%%")))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("合法 Base64");
        assertThatThrownBy(() -> service.recognize(request("data:image/png;base64,QUJDREVGR0g=")))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("声明格式不一致");
        verify(client, never()).recognize(anyString(), anyList());
    }

    @Test
    void rejectsImageOverConfiguredLimit() {
        properties.setMaxImageBytes(7);

        assertThatThrownBy(() -> service.recognize(request(VALID_PNG)))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("不能超过");
        verify(client, never()).recognize(anyString(), anyList());
    }

    private QuestionRecognitionRequest request(String imageBase64) {
        QuestionRecognitionRequest request = new QuestionRecognitionRequest();
        request.setImageBase64(imageBase64);
        return request;
    }

    private Subject subject(Long id, String name) {
        Subject subject = new Subject();
        subject.setId(id);
        subject.setName(name);
        return subject;
    }
}
