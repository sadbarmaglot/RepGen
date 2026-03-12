-- Migration: Add weld seam (СвШ1-СвШ7) and bolt connection (БС1-БС10) defect types

-- Сварные швы
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'weld_seam_corrosion';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'weld_seam_shape_defect';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'weld_seam_lack_of_fusion';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'weld_seam_leg_deviation';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'weld_seam_porosity';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'weld_seam_burn_through';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'weld_seam_cracks';

-- Болтовые соединения
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_corrosion';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_deformation';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_gap';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_incomplete_set';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_grade_deviation';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_nut_loosening';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_missing';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_flange_misalignment';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_shear';
ALTER TYPE defect_type ADD VALUE IF NOT EXISTS 'bolt_flange_thickness_diff';
