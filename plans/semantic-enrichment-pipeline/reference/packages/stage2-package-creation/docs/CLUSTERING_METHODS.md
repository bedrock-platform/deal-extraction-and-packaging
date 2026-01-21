# Clustering Methods Comparison

This document explains the differences between K-means and GMM clustering methods and when to use each.

## Overview

The package supports two clustering methods:

1. **K-Means**: Hard clustering (each deal belongs to one cluster)
2. **GMM (Gaussian Mixture Model)**: Soft clustering (probabilistic assignments)

**GMM is recommended** for most use cases, especially when deal overlap is important.

## K-Means Clustering

### Characteristics

- **Hard Clustering**: Each deal belongs to exactly one cluster
- **Spherical Clusters**: Assumes clusters are roughly spherical
- **Fast**: Quicker than GMM for large datasets
- **Deterministic**: Same input always produces same clusters

### When to Use

- You need hard assignments (each deal in one cluster)
- Clusters are roughly spherical
- You need faster clustering for very large datasets (>10k deals)
- You have a fixed number of clusters

### Example

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="kmeans"
)
```

## GMM Clustering (Recommended)

### Characteristics

- **Soft Clustering**: Probabilistic assignments (deals can belong to multiple clusters)
- **Non-Spherical Clusters**: Handles elliptical/elongated shapes better
- **Auto-Selection**: Automatically finds optimal number of components using BIC
- **Overlap Support**: Naturally supports deal overlap strategy

### Advantages

1. **Better Semantic Grouping**: Captures more nuanced relationships between deals
2. **Deal Overlap**: Soft assignments naturally allow deals in multiple packages
3. **Automatic Tuning**: BIC-based component selection reduces manual tuning
4. **Flexible Shapes**: Handles non-spherical cluster distributions

### When to Use

- You want probabilistic assignments
- Clusters may be non-spherical
- Deal overlap is important
- You want automatic component selection
- **Default choice** for most use cases

### Example

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="gmm"  # Default
)
```

## GMM with Soft Assignments

### Purpose

Enables deal overlap strategy where deals can appear in multiple packages based on probability thresholds.

### How It Works

1. Fits GMM to embeddings
2. Gets probability matrix: `probabilities[deal_idx, component_idx]`
3. Includes deals in clusters where probability >= threshold
4. Deals can appear in multiple clusters

### When to Use

- You want explicit deal overlap
- Deals should appear in multiple packages
- You want to maximize package diversity

### Example

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="gmm",
    use_soft_assignments=True  # Enable probabilistic overlap
)
```

### Probability Threshold

Controls how strict the overlap is:
- **Lower threshold (0.2-0.3)**: More overlap, deals appear in more clusters
- **Higher threshold (0.5-0.7)**: Less overlap, deals appear in fewer clusters
- **Default: 0.3**: Balanced overlap

## Comparison Table

| Feature | K-Means | GMM | GMM (Soft) |
|---------|---------|-----|------------|
| **Clustering Type** | Hard | Soft | Soft |
| **Deal Overlap** | No | Possible | Yes |
| **Cluster Shapes** | Spherical | Flexible | Flexible |
| **Component Selection** | Manual | Auto (BIC) | Auto (BIC) |
| **Speed** | Fast | Moderate | Moderate |
| **Use Case** | Simple grouping | Semantic grouping | Deal overlap |

## Performance Characteristics

### K-Means

- **Time Complexity**: O(N × K × I) where N=deals, K=clusters, I=iterations
- **Typical Performance**: ~1 second for 1000 deals
- **Memory**: Low

### GMM

- **Time Complexity**: O(N × K × D² × I) where D=embedding dimension
- **Typical Performance**: ~3-5 seconds for 1000 deals
- **Memory**: Moderate (stores covariance matrices)

### GMM with Soft Assignments

- **Time Complexity**: Same as GMM + probability calculation
- **Typical Performance**: ~4-6 seconds for 1000 deals
- **Memory**: Higher (stores probability matrix)

## Recommendations

### Default Choice: GMM

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="gmm"  # Best balance of quality and flexibility
)
```

### For Deal Overlap: GMM with Soft Assignments

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="gmm",
    use_soft_assignments=True  # Maximize package diversity
)
```

### For Speed: K-Means

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="kmeans"  # Faster for very large datasets
)
```

## Technical Details

### BIC (Bayesian Information Criterion)

GMM uses BIC to automatically select optimal number of components:

```
BIC = -2 × log_likelihood + k × log(n)
```

Where:
- `log_likelihood`: Model fit quality
- `k`: Number of parameters
- `n`: Number of samples

Lower BIC = Better model (balances fit and complexity)

### Covariance Types

GMM supports different covariance structures:

- **"full"** (default): Each component has its own covariance matrix (most flexible)
- **"tied"**: All components share same covariance matrix
- **"diag"**: Diagonal covariance matrices (faster)
- **"spherical"**: Spherical covariance (fastest, least flexible)

## Best Practices

1. **Start with GMM**: Default choice for most use cases
2. **Enable Soft Assignments**: If deal overlap is important
3. **Adjust Threshold**: Tune probability threshold based on desired overlap
4. **Monitor Performance**: GMM is slower but usually worth it
5. **Use K-Means**: Only if you need hard assignments or speed is critical

## Summary

- **GMM is recommended** for better semantic grouping and deal overlap support
- **K-Means** is faster but less flexible
- **Soft Assignments** enable explicit deal overlap strategy
- **Auto-Selection** (BIC) reduces manual tuning

Choose GMM unless you have specific requirements for hard clustering or speed.
