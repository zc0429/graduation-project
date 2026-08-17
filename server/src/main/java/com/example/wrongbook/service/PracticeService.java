package com.example.wrongbook.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.dto.PracticeRequest;
import com.example.wrongbook.entity.PracticeRecord;

/**
 * 练习记录服务（论文 5.3 类设计 (7)）：保存作答记录并更新掌握度，
 * 答对 +15（上限 100），答错 -20（下限 0），同步写入 question 表
 */
public interface PracticeService {

    /** 提交练习作答（重做错题或完成变式题） */
    Long submit(PracticeRequest request);

    /** 练习记录分页（本人） */
    Page<PracticeRecord> page(Integer pageNum, Integer pageSize);
}
