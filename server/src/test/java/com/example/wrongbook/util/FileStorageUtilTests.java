package com.example.wrongbook.util;

import com.example.wrongbook.common.BizException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.test.util.ReflectionTestUtils;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FileStorageUtilTests {

    @TempDir
    Path uploadDir;

    private FileStorageUtil fileStorageUtil;

    @BeforeEach
    void setUp() {
        fileStorageUtil = new FileStorageUtil();
        ReflectionTestUtils.setField(fileStorageUtil, "uploadDir", uploadDir.toString());
    }

    @Test
    void returnsOwnedImageAsInlineDataAndDeletesReplacedFile() throws Exception {
        byte[] bytes = "GIF89a-final-audit".getBytes();
        String storedPath = fileStorageUtil.saveBase64Image(
                "data:image/gif;base64," + Base64.getEncoder().encodeToString(bytes));

        assertThat(storedPath).startsWith("/uploads/").endsWith(".gif");
        assertThat(fileStorageUtil.readAsDataUrl(storedPath))
                .isEqualTo("data:image/gif;base64," + Base64.getEncoder().encodeToString(bytes));

        fileStorageUtil.deleteIfExists(storedPath);

        try (var files = Files.walk(uploadDir)) {
            assertThat(files.filter(Files::isRegularFile)).isEmpty();
        }
    }

    @Test
    void rejectsUploadPathTraversal() {
        assertThatThrownBy(() -> fileStorageUtil.readAsDataUrl("/uploads/../outside.png"))
                .isInstanceOf(BizException.class)
                .hasMessage("题目图片路径无效");
    }
}
