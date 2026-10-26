package com.example.wrongbook.util;

import com.example.wrongbook.common.BizException;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class QuestionContentTests {

    @Test
    void keepsLegacyMathematicalTextWithoutInterpretingComparisonsAsTags() {
        String text = "已知 0 < x < 3，A & B\n求 x²。";
        assertThat(QuestionContent.validatedStem(text)).isEqualTo(text);
        assertThat(QuestionContent.plainText(text)).isEqualTo(text);
    }

    @Test
    void removesActiveContentAndAllAttributesButPreservesSupportedFormatting() {
        String clean = QuestionContent.validatedStem("<p onclick='x()' style='color:red'>题<strong>干</strong>"
                + "<script>alert(1)</script><img src=x onerror='x()'><a href='javascript:x()'>条件</a></p>");
        assertThat(clean).isEqualTo("<p>题<strong>干</strong>条件</p>");
        assertThat(QuestionContent.plainText(clean)).isEqualTo("题干条件");
    }

    @Test
    void normalizesParagraphsListsAndMathematicalIndicesForAiAndExport() {
        assertThat(QuestionContent.plainText("<p>求 x<sup>2</sup> + H<sub>2</sub>O</p>"
                + "<ol><li>A</li><li>B<br>C</li></ol>"))
                .isEqualTo("求 x^(2) + H_(2)O\nA\nB\nC");
    }

    @Test
    void refusesEmptyRichTextAndExcessiveInput() {
        assertThatThrownBy(() -> QuestionContent.validatedStem("<p><br>&nbsp;</p>"))
                .isInstanceOf(BizException.class).hasMessage("题干不能为空");
        assertThatThrownBy(() -> QuestionContent.validatedStem("<p>" + "题".repeat(2001) + "</p>"))
                .isInstanceOf(BizException.class).hasMessageContaining("2000");
        assertThatThrownBy(() -> QuestionContent.validatedStem(" ".repeat(24001)))
                .isInstanceOf(BizException.class).hasMessageContaining("格式内容过长");
    }
}
