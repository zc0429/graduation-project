package com.example.wrongbook.vo;
import java.util.List;
public record PracticeProgressVO(boolean originalPracticed, List<Long> practicedVariantIds) {}
