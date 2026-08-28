package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.config.ImageRecognitionProperties;
import com.example.wrongbook.dto.QuestionRecognitionRequest;
import com.example.wrongbook.entity.Subject;
import com.example.wrongbook.service.QuestionRecognitionClient;
import com.example.wrongbook.service.QuestionRecognitionService;
import com.example.wrongbook.service.SubjectService;
import com.example.wrongbook.vo.QuestionRecognitionResult;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class QuestionRecognitionServiceImpl implements QuestionRecognitionService {

    private static final Pattern IMAGE_DATA_URI = Pattern.compile(
            "^data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/]+={0,2})$",
            Pattern.CASE_INSENSITIVE);

    private final ImageRecognitionProperties properties;
    private final ObjectProvider<QuestionRecognitionClient> recognitionClientProvider;
    private final SubjectService subjectService;

    @Override
    public QuestionRecognitionResult recognize(QuestionRecognitionRequest request) {
        if (!properties.isEnabled()) {
            throw new BizException("图片识别功能未启用，可继续手工录入");
        }
        validateImage(request.getImageBase64());

        List<Subject> subjects = subjectService.list();
        Map<String, Subject> subjectsByName = new LinkedHashMap<>();
        for (Subject subject : subjects) {
            if (subject.getId() != null && StringUtils.hasText(subject.getName())) {
                subjectsByName.put(normalizeSubjectName(subject.getName()), subject);
            }
        }
        if (subjectsByName.isEmpty()) {
            throw new BizException("当前没有可用科目，请先手工维护科目");
        }

        QuestionRecognitionClient client = recognitionClientProvider.getIfAvailable();
        if (client == null) {
            throw new BizException("图片识别服务未就绪，可继续手工录入");
        }
        QuestionRecognitionClient.Extraction extraction = client.recognize(
                request.getImageBase64(),
                subjects.stream().map(Subject::getName).filter(StringUtils::hasText).toList());

        Subject matchedSubject = StringUtils.hasText(extraction.subjectName())
                ? subjectsByName.get(normalizeSubjectName(extraction.subjectName()))
                : null;
        return new QuestionRecognitionResult(
                matchedSubject == null ? null : matchedSubject.getId(),
                matchedSubject == null ? null : matchedSubject.getName(),
                extraction.stem(),
                emptyToNull(extraction.studentAnswer()),
                emptyToNull(extraction.source()));
    }

    private void validateImage(String imageDataUrl) {
        if (!StringUtils.hasText(imageDataUrl)) {
            throw new BizException("请选择需要识别的题目图片");
        }
        int maxBytes = properties.getMaxImageBytes();
        if (maxBytes <= 0) {
            throw new IllegalStateException("图片识别大小上限必须大于 0");
        }
        Matcher matcher = IMAGE_DATA_URI.matcher(imageDataUrl);
        if (!matcher.matches()) {
            throw new BizException("图片识别仅支持 JPG、PNG 或 WebP 的合法 Base64 数据");
        }
        String encoded = matcher.group(2);
        int maxEncodedLength = ((maxBytes + 2) / 3) * 4;
        if (encoded.length() > maxEncodedLength) {
            throw new BizException("用于 AI 识别的图片不能超过 " + maxBytes / 1024 / 1024 + "MB");
        }

        byte[] bytes;
        try {
            bytes = Base64.getDecoder().decode(encoded.getBytes(StandardCharsets.US_ASCII));
        } catch (IllegalArgumentException e) {
            throw new BizException("图片 Base64 数据无效");
        }
        if (bytes.length == 0 || bytes.length > maxBytes) {
            throw new BizException("用于 AI 识别的图片不能超过 " + maxBytes / 1024 / 1024 + "MB");
        }
        String mime = matcher.group(1).toLowerCase(Locale.ROOT);
        if (!matchesSignature(mime, bytes)) {
            throw new BizException("图片内容与声明格式不一致");
        }
    }

    private boolean matchesSignature(String mime, byte[] bytes) {
        return switch (mime) {
            case "jpeg" -> bytes.length >= 3
                    && unsigned(bytes[0]) == 0xFF && unsigned(bytes[1]) == 0xD8 && unsigned(bytes[2]) == 0xFF;
            case "png" -> bytes.length >= 8
                    && unsigned(bytes[0]) == 0x89 && bytes[1] == 0x50 && bytes[2] == 0x4E && bytes[3] == 0x47
                    && bytes[4] == 0x0D && bytes[5] == 0x0A && bytes[6] == 0x1A && bytes[7] == 0x0A;
            case "webp" -> bytes.length >= 12
                    && ascii(bytes, 0, "RIFF") && ascii(bytes, 8, "WEBP");
            default -> false;
        };
    }

    private boolean ascii(byte[] bytes, int offset, String expected) {
        for (int i = 0; i < expected.length(); i++) {
            if (bytes[offset + i] != (byte) expected.charAt(i)) {
                return false;
            }
        }
        return true;
    }

    private int unsigned(byte value) {
        return value & 0xFF;
    }

    private String normalizeSubjectName(String value) {
        return value.trim().toLowerCase(Locale.ROOT);
    }

    private String emptyToNull(String value) {
        return StringUtils.hasText(value) ? value.trim() : null;
    }
}
