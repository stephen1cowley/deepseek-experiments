for i in {1..10}; do
    for j in {0..10}; do
        sbatch simplebench_eval_40mins.wilkes3 $i $j
    done
done