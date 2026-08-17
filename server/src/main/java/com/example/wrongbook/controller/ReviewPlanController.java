package com.example.wrongbook.controller;

import com.example.wrongbook.common.RestResponse;
import com.example.wrongbook.service.ReviewPlanService;
import com.example.wrongbook.vo.ReviewPlanVO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/review-plan")
@RequiredArgsConstructor
public class ReviewPlanController {

    private final ReviewPlanService reviewPlanService;

    @GetMapping("/today")
    public RestResponse<List<ReviewPlanVO>> today() {
        return RestResponse.ok(reviewPlanService.today());
    }

    @PutMapping("/{id}/finish")
    public RestResponse<Void> finish(@PathVariable Long id) {
        reviewPlanService.finish(id);
        return RestResponse.ok();
    }
}
