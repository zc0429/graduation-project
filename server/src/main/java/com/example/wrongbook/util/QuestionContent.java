package com.example.wrongbook.util;

import com.example.wrongbook.common.BizException;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.TextNode;
import org.jsoup.safety.Safelist;

import java.util.regex.Pattern;

/** Compatible storage in the existing stem TEXT column; no historical rewrite. */
public final class QuestionContent {

    private static final Safelist ALLOWED = new Safelist().addTags(
            "p", "br", "strong", "b", "em", "i", "u", "s", "strike", "del", "ul", "ol", "li", "sub", "sup");
    private static final Pattern MARKUP = Pattern.compile(
            "<\\s*/?\\s*(?:p|br|strong|b|em|i|u|s|strike|del|ul|ol|li|sub|sup|script|style|img|svg|math|iframe|object|embed|div|span)\\b[^>]*>",
            Pattern.CASE_INSENSITIVE);

    private QuestionContent() {
    }

    public static String sanitize(String input) {
        if (input == null) {
            return "";
        }
        if (!MARKUP.matcher(input).find()) {
            return input.replace("\r\n", "\n").replace('\r', '\n').trim();
        }
        return Jsoup.clean(input, "", ALLOWED, new Document.OutputSettings().prettyPrint(false)).trim();
    }

    public static String validatedStem(String input) {
        if (input != null && input.length() > 24000) {
            throw new BizException("题干格式内容过长，请精简后保存");
        }
        String clean = sanitize(input);
        String text = plainText(clean);
        if (text.isBlank()) {
            throw new BizException("题干不能为空");
        }
        if (text.length() > 2000) {
            throw new BizException("题干不能超过 2000 字");
        }
        return clean;
    }

    /** Preserve paragraph boundaries and mathematical indices in prompts/exports. */
    public static String plainText(String input) {
        if (input == null) {
            return "";
        }
        if (!MARKUP.matcher(input).find()) {
            return input.replace("\r\n", "\n").replace('\r', '\n').trim();
        }
        Element body = Jsoup.parseBodyFragment(sanitize(input)).body();
        for (Element index : body.select("sup, sub")) {
            index.replaceWith(new TextNode((index.tagName().equals("sup") ? "^(" : "_(") + index.text() + ")"));
        }
        body.select("br").forEach(element -> element.replaceWith(new TextNode("\n")));
        body.select("p, li, ul, ol").forEach(element -> element.appendChild(new TextNode("\n")));
        return body.wholeText().replace('\u00a0', ' ').replaceAll("\\n{3,}", "\n\n").trim();
    }
}
