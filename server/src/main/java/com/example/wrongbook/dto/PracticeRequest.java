package com.example.wrongbook.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PracticeRequest {

    /** 重做的错题（与 variantId 二选一） */
    private Long questionId;

    /** 作答的变式题（与 questionId 二选一） */
    private Long variantId;

    private String userAnswer;

    /** 是否正确：1 正确，0 错误 */
    @NotNull(message = "作答结果不能为空")
    private Integer isCorrect;

    /** 作答用时（秒） */
    private Integer duration;
}
