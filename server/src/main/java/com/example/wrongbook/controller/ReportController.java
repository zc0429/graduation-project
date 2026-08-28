package com.example.wrongbook.controller;

import com.example.wrongbook.common.RequireRole;
import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.service.ReportService;
import com.example.wrongbook.vo.WeeklyReportVO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/report")
@RequiredArgsConstructor
@RequireRole({"student", "teacher"})
public class ReportController {

    private final ReportService reportService;

    @GetMapping("/weekly")
    public RestResponse<WeeklyReportVO> weekly() {
        return RestResponse.ok(reportService.weekly());
    }

    @PostMapping("/generate")
    public RestResponse<WeeklyReportVO> generate() {
        return RestResponse.ok(reportService.generate());
    }
}
