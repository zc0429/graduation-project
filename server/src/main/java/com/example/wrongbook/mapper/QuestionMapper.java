package com.example.wrongbook.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.wrongbook.entity.Question;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public interface QuestionMapper extends BaseMapper<Question> {

    /** 在短事务内锁定正常题目，防止派生数据基于过期输入回写。 */
    @Select("SELECT * FROM question WHERE id = #{id} AND status = 1 FOR UPDATE")
    Question selectByIdForUpdate(@Param("id") Long id);

    /** 读取全部正常题目的向量维护快照。 */
    @Select("""
            SELECT id, user_id, subject_id, knowledge_point_id, stem, embedding
            FROM question
            WHERE status = 1
            ORDER BY id
            """)
    List<Question> selectActiveEmbeddingSnapshots();

    /** 仅当题干快照仍完全一致时回写向量，避免维护任务覆盖并发编辑后的题目。 */
    @Update("""
            UPDATE question
            SET embedding = #{embedding}
            WHERE id = #{id}
              AND status = 1
              AND BINARY stem = BINARY #{stem}
            """)
    int updateEmbeddingIfStemUnchanged(
            @Param("id") Long id,
            @Param("stem") String stem,
            @Param("embedding") String embedding);

    /** 按知识点分组统计掌握度（学情报告，论文 5.4 自定义聚合 SQL） */
    List<Map<String, Object>> selectKpMastery(@Param("userId") Long userId);

    /** 按日统计新增错题数（since 起） */
    List<Map<String, Object>> selectDailyCount(@Param("userId") Long userId, @Param("since") LocalDateTime since);
}
